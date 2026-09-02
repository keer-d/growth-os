"""Approved Web query retrieval through a generic public search API.

The business surface names the **channel** ("Web"), never the vendor, so every
public name here is vendor-neutral and the adapter maps a generic result-list
shape: swapping the search vendor is a provider change, not an adapter change.
"""

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

from domain.models import RawCreatorProfile, utc_now_iso
from domain.query_review import ApprovedSearchPlan, ApprovedSearchQuery
from domain.retrieval import DiscoveryQueryResult, DiscoveryRunResult
from pipeline.normalize import normalize_profile_url
from pipeline.tls import trusted_ssl_context


DEFAULT_WEB_SEARCH_BASE_URL = "https://www.googleapis.com/customsearch/v1"
DEFAULT_RESULTS_PER_QUERY = 3
MAX_RESULTS_PER_QUERY = 10

# Search vendors disagree on the envelope key and on the field names inside each
# entry; reading all of them keeps one vendor's spelling out of the mapping.
_RESULT_LIST_KEYS = ("items", "results", "organic_results")
_LINK_KEYS = ("link", "url")
_TITLE_KEYS = ("title",)
_SNIPPET_KEYS = ("snippet", "description")


class WebProviderError(RuntimeError):
    """A web search provider request failed with a safe, machine-readable code."""

    def __init__(self, error_code: str, safe_message: str):
        super().__init__(safe_message)
        self.error_code = error_code
        self.safe_message = safe_message


class WebProviderConfigurationError(WebProviderError):
    """Web live configuration is missing or invalid."""


class WebSearchProvider(ABC):
    connector_name: str

    @abstractmethod
    def search(self, query_text: str, limit: int) -> dict[str, Any]:
        """Return one raw web search response without inferring partner quality."""


@dataclass(frozen=True, repr=False)
class WebSearchConfiguration:
    api_key: str
    base_url: str = DEFAULT_WEB_SEARCH_BASE_URL
    engine_id: str | None = None
    timeout_seconds: int = 60

    def __post_init__(self) -> None:
        if not isinstance(self.api_key, str) or not self.api_key.strip():
            raise WebProviderConfigurationError(
                "configuration_missing",
                "WEB_SEARCH_API_KEY is required for Web live retrieval",
            )
        if not isinstance(self.base_url, str) or not self.base_url.startswith("https://"):
            raise WebProviderConfigurationError(
                "invalid_provider_configuration",
                "WEB_SEARCH_BASE_URL must be an HTTPS URL",
            )
        if self.engine_id is not None and (
            not isinstance(self.engine_id, str) or not self.engine_id.strip()
        ):
            raise WebProviderConfigurationError(
                "invalid_provider_configuration",
                "WEB_SEARCH_ENGINE_ID must be null or a non-empty string",
            )
        if not 10 <= self.timeout_seconds <= 180:
            raise WebProviderConfigurationError(
                "invalid_provider_configuration",
                "WEB_SEARCH_TIMEOUT_SECONDS must be between 10 and 180",
            )

    @classmethod
    def from_environment(cls) -> "WebSearchConfiguration":
        return cls(
            api_key=os.getenv("WEB_SEARCH_API_KEY", "").strip(),
            base_url=(
                os.getenv("WEB_SEARCH_BASE_URL", "").strip()
                or DEFAULT_WEB_SEARCH_BASE_URL
            ),
            engine_id=os.getenv("WEB_SEARCH_ENGINE_ID", "").strip() or None,
            timeout_seconds=_environment_int("WEB_SEARCH_TIMEOUT_SECONDS", 60),
        )


class WebSearchAPIProvider(WebSearchProvider):
    """Thin client for one public web search result page."""

    connector_name = "web_search_api_v1"

    def __init__(self, configuration: WebSearchConfiguration):
        self.configuration = configuration

    def search(self, query_text: str, limit: int) -> dict[str, Any]:
        if not isinstance(query_text, str) or not query_text.strip():
            raise WebProviderError("invalid_query", "approved query text must be non-empty")
        if not 1 <= limit <= MAX_RESULTS_PER_QUERY:
            raise WebProviderError(
                "invalid_result_limit",
                f"result limit must be between 1 and {MAX_RESULTS_PER_QUERY}",
            )
        parameters: dict[str, Any] = {"key": self.configuration.api_key}
        # A scoped engine is optional: vendors without one accept key/q/num alone.
        if self.configuration.engine_id:
            parameters["cx"] = self.configuration.engine_id
        parameters["q"] = query_text.strip()
        parameters["num"] = limit
        endpoint = (
            self.configuration.base_url.rstrip("/") + "?" + urlencode(parameters)
        )
        request = Request(endpoint, headers={"Accept": "application/json"})
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
            raise WebProviderError(
                "provider_timeout", "web search request timed out"
            ) from exc
        except SSLError as exc:
            raise WebProviderError(
                "provider_tls_failure", "web search TLS certificate validation failed"
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, (TimeoutError, SocketTimeout)):
                code = "provider_timeout"
                message = "web search request timed out"
            elif isinstance(exc.reason, (SSLCertVerificationError, SSLError)):
                code = "provider_tls_failure"
                message = "web search TLS certificate validation failed"
            else:
                code = "provider_network_failure"
                message = "web search request failed due to a network error"
            raise WebProviderError(code, message) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WebProviderError(
                "malformed_provider_response", "web search response was not valid JSON"
            ) from exc
        if not isinstance(data, dict):
            raise WebProviderError(
                "malformed_provider_response", "web search response must be an object"
            )
        return data

    @staticmethod
    def _http_error(exc: HTTPError) -> WebProviderError:
        status = exc.code
        exc.close()
        if status in {401, 403}:
            return WebProviderError(
                "provider_authentication_failure",
                "web search rejected the credential or its permissions",
            )
        if status == 408:
            return WebProviderError("provider_timeout", "web search request timed out")
        if status in {402, 429}:
            return WebProviderError(
                "provider_rate_limit_or_quota",
                "web search rate limit, quota, or access tier blocked the request",
            )
        return WebProviderError(
            "provider_http_failure", f"web search request failed with HTTP {status}"
        )


class WebLiveRetrievalAdapter:
    """Map public web search results into the shared raw creator contract."""

    def __init__(
        self,
        provider: WebSearchProvider,
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
            raise TypeError("Web retrieval requires an ApprovedSearchPlan")
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("run_id must be a non-empty string")
        if query_limit is not None and query_limit < 1:
            raise ValueError("query_limit must be positive when provided")

        started_at = utc_now_iso()
        queries = [query for query in approved_plan.queries if query.platform == "web"]
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
        except WebProviderError as exc:
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
                f"web search provider failed with {exc.__class__.__name__}",
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
                error_message="web search returned results, but none were valid partner records",
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
            raise WebProviderError(
                "malformed_provider_response", "web search response must be an object"
            )
        entries = _result_entries(response)
        if entries is None or entries == []:
            if response.get("error") or response.get("errors"):
                raise WebProviderError(
                    "provider_http_failure",
                    "web search returned a structured provider error",
                )
            return [], [], 0
        if not isinstance(entries, list) or any(
            not isinstance(item, dict) for item in entries
        ):
            raise WebProviderError(
                "malformed_provider_response",
                "web search results must be an array of result objects",
            )

        retrieved_at = utc_now_iso()
        profiles: list[RawCreatorProfile] = []
        invalid_reasons: list[str] = []
        seen: set[str] = set()
        candidate_count = 0
        for index, entry in enumerate(entries):
            if candidate_count >= self.results_per_query:
                break
            try:
                link = _first_text(entry, _LINK_KEYS)
                if link is None:
                    raise ValueError("provider field link is missing")
                # Raises for search hosts and for links a channel connector already
                # owns, which is how a social profile found on the web is stopped
                # from counting the same partner twice.
                normalized = normalize_profile_url(link, "web")
                # The same canonical site repeated in one result page is one
                # partner, not a second observation, so it is not counted at all.
                if normalized in seen:
                    continue
                profile = self._map_profile(
                    entry,
                    link=link,
                    normalized_profile_url=normalized,
                    approved_plan=approved_plan,
                    query=query,
                    run_id=run_id,
                    retrieved_at=retrieved_at,
                )
            except (TypeError, ValueError) as exc:
                candidate_count += 1
                invalid_reasons.append(
                    f"provider result {index} was not a valid web partner: {exc}"
                )
                continue
            seen.add(normalized)
            candidate_count += 1
            profiles.append(profile)
        return profiles, invalid_reasons, candidate_count

    def _map_profile(
        self,
        entry: dict[str, Any],
        *,
        link: str,
        normalized_profile_url: str,
        approved_plan: ApprovedSearchPlan,
        query: ApprovedSearchQuery,
        run_id: str,
        retrieved_at: str,
    ) -> RawCreatorProfile:
        signature = f"{run_id}|{query.query_id}|{normalized_profile_url}"
        return RawCreatorProfile(
            record_id=f"web_{sha256(signature.encode('utf-8')).hexdigest()[:16]}",
            platform="web",
            profile_url=link,
            normalized_profile_url=normalized_profile_url,
            display_name=_first_text(entry, _TITLE_KEYS),
            bio_text=_first_text(entry, _SNIPPET_KEYS),
            # The open web has no follower concept; an invented number would be
            # read downstream as an observed fact.
            follower_count=None,
            external_urls=(
                (link,) if link.startswith(("https://", "http://")) else ()
            ),
            # The snippet is already the bio — repeating it as content would
            # double-count one observation in the signal layer.
            content_samples=(),
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
            "platform": "web",
            "query_text": query.query_text,
            "search_angle": query.search_angle,
            "run_id": run_id,
        }


def _result_entries(response: dict[str, Any]) -> Any:
    for key in _RESULT_LIST_KEYS:
        if key in response:
            return response[key]
    return None


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _first_text(entry: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        text = _optional_text(entry.get(key))
        if text is not None:
            return text
    return None


def _environment_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise WebProviderConfigurationError(
            "invalid_provider_configuration", f"{name} must be an integer"
        ) from exc
