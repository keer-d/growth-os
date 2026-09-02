"""Approved X query retrieval through the official X API v2."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from socket import timeout as SocketTimeout
from ssl import SSLCertVerificationError, SSLError
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from domain.models import ContentSample, RawCreatorProfile, utc_now_iso
from domain.query_review import ApprovedSearchPlan, ApprovedSearchQuery
from domain.retrieval import DiscoveryQueryResult, DiscoveryRunResult
from pipeline.normalize import normalize_profile_url
from pipeline.tls import trusted_ssl_context


DEFAULT_X_API_BASE_URL = "https://api.x.com/2"
DEFAULT_RESULTS_PER_QUERY = 3
MAX_RESULTS_PER_QUERY = 10


class XProviderError(RuntimeError):
    """An X provider request failed with a safe, machine-readable code."""

    def __init__(self, error_code: str, safe_message: str):
        super().__init__(safe_message)
        self.error_code = error_code
        self.safe_message = safe_message


class XProviderConfigurationError(XProviderError):
    """X live configuration is missing or invalid."""


class XProfileSearchProvider(ABC):
    connector_name: str

    @abstractmethod
    def search(self, query_text: str, limit: int) -> dict[str, Any]:
        """Return one raw recent-search response without inferring creator quality."""


@dataclass(frozen=True, repr=False)
class XAPIConfiguration:
    bearer_token: str
    base_url: str = DEFAULT_X_API_BASE_URL
    timeout_seconds: int = 60

    def __post_init__(self) -> None:
        if not isinstance(self.bearer_token, str) or not self.bearer_token.strip():
            raise XProviderConfigurationError(
                "configuration_missing", "X_BEARER_TOKEN is required for X live retrieval"
            )
        if not isinstance(self.base_url, str) or not self.base_url.startswith("https://"):
            raise XProviderConfigurationError(
                "invalid_provider_configuration",
                "X_API_BASE_URL must be an HTTPS URL",
            )
        if not 10 <= self.timeout_seconds <= 180:
            raise XProviderConfigurationError(
                "invalid_provider_configuration",
                "X_API_TIMEOUT_SECONDS must be between 10 and 180",
            )

    @classmethod
    def from_environment(cls) -> "XAPIConfiguration":
        return cls(
            bearer_token=os.getenv("X_BEARER_TOKEN", "").strip(),
            base_url=(
                os.getenv("X_API_BASE_URL", "").strip() or DEFAULT_X_API_BASE_URL
            ),
            timeout_seconds=_environment_int("X_API_TIMEOUT_SECONDS", 60),
        )


class XRecentSearchProvider(XProfileSearchProvider):
    """Thin client for public recent Posts with author expansions."""

    connector_name = "x_api_v2_recent_search"

    def __init__(self, configuration: XAPIConfiguration):
        self.configuration = configuration

    def search(self, query_text: str, limit: int) -> dict[str, Any]:
        if not isinstance(query_text, str) or not query_text.strip():
            raise XProviderError("invalid_query", "approved query text must be non-empty")
        if not 1 <= limit <= MAX_RESULTS_PER_QUERY:
            raise XProviderError(
                "invalid_result_limit",
                f"result limit must be between 1 and {MAX_RESULTS_PER_QUERY}",
            )
        parameters = urlencode(
            {
                "query": query_text.strip(),
                "max_results": 10,
                "expansions": "author_id",
                "tweet.fields": "author_id,created_at",
                "user.fields": "id,name,username,description,public_metrics,url,entities",
            }
        )
        endpoint = (
            self.configuration.base_url.rstrip("/")
            + "/tweets/search/recent?"
            + parameters
        )
        request = Request(
            endpoint,
            headers={
                "Authorization": f"Bearer {self.configuration.bearer_token}",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(
                request,
                timeout=self.configuration.timeout_seconds,
                context=trusted_ssl_context(),
            ) as response:
                body = response.read().decode("utf-8")
            data = json.loads(body)
        except HTTPError as exc:
            raise self._http_error(exc) from exc
        except (TimeoutError, SocketTimeout) as exc:
            raise XProviderError("provider_timeout", "X API request timed out") from exc
        except SSLError as exc:
            raise XProviderError(
                "provider_tls_failure", "X API TLS certificate validation failed"
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, (TimeoutError, SocketTimeout)):
                code = "provider_timeout"
                message = "X API request timed out"
            elif isinstance(exc.reason, (SSLCertVerificationError, SSLError)):
                code = "provider_tls_failure"
                message = "X API TLS certificate validation failed"
            else:
                code = "provider_network_failure"
                message = "X API request failed due to a network error"
            raise XProviderError(code, message) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise XProviderError(
                "malformed_provider_response", "X API response was not valid JSON"
            ) from exc
        if not isinstance(data, dict):
            raise XProviderError(
                "malformed_provider_response", "X API response must be an object"
            )
        return data

    @staticmethod
    def _http_error(exc: HTTPError) -> XProviderError:
        status = exc.code
        exc.close()
        if status in {401, 403}:
            return XProviderError(
                "provider_authentication_failure",
                "X API rejected the credential or its permissions",
            )
        if status == 408:
            return XProviderError("provider_timeout", "X API request timed out")
        if status in {402, 429}:
            return XProviderError(
                "provider_rate_limit_or_quota",
                "X API rate limit, quota, or access tier blocked the request",
            )
        return XProviderError(
            "provider_http_failure", f"X API request failed with HTTP {status}"
        )


class XLiveRetrievalAdapter:
    """Map public X recent-search results into the shared raw creator contract."""

    def __init__(
        self,
        provider: XProfileSearchProvider,
        *,
        results_per_query: int = DEFAULT_RESULTS_PER_QUERY,
    ):
        if not 1 <= results_per_query <= MAX_RESULTS_PER_QUERY:
            raise ValueError(
                f"results_per_query must be between 1 and {MAX_RESULTS_PER_QUERY}"
            )
        self.provider = provider
        self.results_per_query = results_per_query

    def retrieve(
        self,
        approved_plan: ApprovedSearchPlan,
        *,
        run_id: str,
        query_limit: int | None = None,
    ) -> DiscoveryRunResult:
        if not isinstance(approved_plan, ApprovedSearchPlan) or approved_plan.status != "approved":
            raise TypeError("X retrieval requires an ApprovedSearchPlan")
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("run_id must be a non-empty string")
        if query_limit is not None and query_limit < 1:
            raise ValueError("query_limit must be positive when provided")

        started_at = utc_now_iso()
        queries = [query for query in approved_plan.queries if query.platform == "x"]
        if query_limit is not None:
            queries = queries[:query_limit]
        results = tuple(
            self._retrieve_query(approved_plan, query, run_id.strip())
            for query in queries
        )
        return DiscoveryRunResult(
            run_id=run_id.strip(),
            campaign_id=approved_plan.campaign_id,
            approved_search_plan_id=approved_plan.approved_search_plan_id,
            discovery_mode="live",
            query_results=results,
            started_at=started_at,
            completed_at=utc_now_iso(),
        )

    def _retrieve_query(
        self,
        approved_plan: ApprovedSearchPlan,
        query: ApprovedSearchQuery,
        run_id: str,
    ) -> DiscoveryQueryResult:
        started_at = utc_now_iso()
        try:
            response = self.provider.search(query.query_text, self.results_per_query)
            profiles, invalid_reasons, candidate_count = self._map_response(
                response,
                approved_plan=approved_plan,
                query=query,
                run_id=run_id,
            )
        except XProviderError as exc:
            return self._failure(
                approved_plan, query, run_id, started_at, exc.error_code, exc.safe_message
            )
        except Exception as exc:
            return self._failure(
                approved_plan,
                query,
                run_id,
                started_at,
                "unexpected_provider_failure",
                f"X provider failed with {exc.__class__.__name__}",
            )

        if candidate_count and not profiles:
            return DiscoveryQueryResult(
                **self._base_fields(approved_plan, query, run_id),
                source_connector=self.provider.connector_name,
                status="FAILED",
                profiles=(),
                provider_result_count=candidate_count,
                invalid_result_count=len(invalid_reasons),
                invalid_result_reasons=tuple(invalid_reasons),
                started_at=started_at,
                completed_at=utc_now_iso(),
                error_code="invalid_creator_record",
                error_message="X returned results, but none were valid creator records",
            )
        status = "SUCCESS_WITH_RESULTS" if profiles else "SUCCESS_ZERO_RESULTS"
        return DiscoveryQueryResult(
            **self._base_fields(approved_plan, query, run_id),
            source_connector=self.provider.connector_name,
            status=status,
            profiles=tuple(profiles),
            provider_result_count=candidate_count,
            invalid_result_count=len(invalid_reasons),
            invalid_result_reasons=tuple(invalid_reasons),
            started_at=started_at,
            completed_at=utc_now_iso(),
        )

    def _map_response(
        self,
        response: Any,
        *,
        approved_plan: ApprovedSearchPlan,
        query: ApprovedSearchQuery,
        run_id: str,
    ) -> tuple[list[RawCreatorProfile], list[str], int]:
        if not isinstance(response, dict):
            raise XProviderError(
                "malformed_provider_response", "X API response must be an object"
            )
        posts = response.get("data")
        if posts is None:
            if response.get("errors"):
                raise XProviderError(
                    "provider_http_failure", "X API returned a structured provider error"
                )
            return [], [], 0
        if not isinstance(posts, list) or any(not isinstance(item, dict) for item in posts):
            raise XProviderError(
                "malformed_provider_response", "X API data must be an array of Posts"
            )
        if not posts:
            if response.get("errors"):
                raise XProviderError(
                    "provider_http_failure", "X API returned a structured provider error"
                )
            return [], [], 0
        includes = response.get("includes")
        users = includes.get("users") if isinstance(includes, dict) else None
        if not isinstance(users, list) or any(not isinstance(item, dict) for item in users):
            raise XProviderError(
                "malformed_provider_response",
                "X API author expansion was missing or malformed",
            )
        users_by_id = {
            str(user.get("id")): user for user in users if user.get("id") is not None
        }
        author_ids: list[str] = []
        for post in posts:
            author_id = post.get("author_id")
            if author_id is None:
                raise XProviderError(
                    "malformed_provider_response", "X API Post was missing author_id"
                )
            author_id = str(author_id)
            if author_id not in author_ids:
                author_ids.append(author_id)
            if len(author_ids) >= self.results_per_query:
                break

        retrieved_at = utc_now_iso()
        profiles: list[RawCreatorProfile] = []
        invalid_reasons: list[str] = []
        for index, author_id in enumerate(author_ids):
            user = users_by_id.get(author_id)
            try:
                if user is None:
                    raise ValueError("expanded author was missing")
                profiles.append(
                    self._map_profile(
                        user,
                        [post for post in posts if str(post.get("author_id")) == author_id],
                        approved_plan=approved_plan,
                        query=query,
                        run_id=run_id,
                        retrieved_at=retrieved_at,
                    )
                )
            except (TypeError, ValueError) as exc:
                invalid_reasons.append(
                    f"provider result {index} was not a valid X creator: {exc}"
                )
        return profiles, invalid_reasons, len(author_ids)

    def _map_profile(
        self,
        user: dict[str, Any],
        posts: list[dict[str, Any]],
        *,
        approved_plan: ApprovedSearchPlan,
        query: ApprovedSearchQuery,
        run_id: str,
        retrieved_at: str,
    ) -> RawCreatorProfile:
        username = _required_text(user.get("username"), "username")
        profile_url = f"https://x.com/{username}"
        signature = f"{run_id}|{query.query_id}|{profile_url}"
        return RawCreatorProfile(
            record_id=f"x_{sha256(signature.encode('utf-8')).hexdigest()[:16]}",
            platform="x",
            profile_url=profile_url,
            normalized_profile_url=normalize_profile_url(profile_url, "x"),
            display_name=_optional_text(user.get("name")),
            bio_text=_optional_text(user.get("description")),
            follower_count=_followers_count(user.get("public_metrics")),
            external_urls=_user_external_urls(user),
            content_samples=tuple(_content_sample(post, username) for post in posts if post.get("text")),
            discovery_mode="live",
            source_connector=self.provider.connector_name,
            run_id=run_id,
            query_id=query.query_id,
            retrieved_at=retrieved_at,
            campaign_id=approved_plan.campaign_id,
            approved_search_plan_id=approved_plan.approved_search_plan_id,
            source_query_id=query.source_query_id,
            query_text=query.query_text,
            search_angle=query.search_angle,
        )

    def _failure(
        self,
        approved_plan: ApprovedSearchPlan,
        query: ApprovedSearchQuery,
        run_id: str,
        started_at: str,
        error_code: str,
        error_message: str,
    ) -> DiscoveryQueryResult:
        return DiscoveryQueryResult(
            **self._base_fields(approved_plan, query, run_id),
            source_connector=self.provider.connector_name,
            status="FAILED",
            profiles=(),
            provider_result_count=0,
            invalid_result_count=0,
            invalid_result_reasons=(),
            started_at=started_at,
            completed_at=utc_now_iso(),
            error_code=error_code,
            error_message=error_message,
        )

    @staticmethod
    def _base_fields(
        approved_plan: ApprovedSearchPlan,
        query: ApprovedSearchQuery,
        run_id: str,
    ) -> dict[str, str]:
        return {
            "campaign_id": approved_plan.campaign_id,
            "approved_search_plan_id": approved_plan.approved_search_plan_id,
            "query_id": query.query_id,
            "source_query_id": query.source_query_id,
            "platform": "x",
            "query_text": query.query_text,
            "search_angle": query.search_angle,
            "run_id": run_id,
        }


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"provider field {field_name} is missing")
    return value.strip()


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _followers_count(value: Any) -> int | None:
    if not isinstance(value, dict):
        return None
    followers = value.get("followers_count")
    if isinstance(followers, bool) or not isinstance(followers, int) or followers < 0:
        return None
    return followers


def _content_sample(post: dict[str, Any], username: str) -> ContentSample:
    post_id = post.get("id")
    url = f"https://x.com/{username}/status/{post_id}" if post_id is not None else None
    return ContentSample(
        text=_required_text(post.get("text"), "Post text"),
        url=url,
        published_at=_optional_text(post.get("created_at")),
    )


def _user_external_urls(user: dict[str, Any]) -> tuple[str, ...]:
    candidates: list[str] = []
    direct = user.get("url")
    if isinstance(direct, str):
        candidates.append(direct)
    entities = user.get("entities")
    if isinstance(entities, dict):
        for section in entities.values():
            if not isinstance(section, dict):
                continue
            urls = section.get("urls")
            if not isinstance(urls, list):
                continue
            for entry in urls:
                if isinstance(entry, dict):
                    expanded = entry.get("expanded_url") or entry.get("url")
                    if isinstance(expanded, str):
                        candidates.append(expanded)
    return tuple(
        dict.fromkeys(
            value.strip()
            for value in candidates
            if value.strip().startswith(("https://", "http://"))
        )
    )


def _environment_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise XProviderConfigurationError(
            "invalid_provider_configuration", f"{name} must be an integer"
        ) from exc
