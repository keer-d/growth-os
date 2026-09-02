"""Approved YouTube query retrieval through the public YouTube Data API v3."""

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


DEFAULT_YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"
DEFAULT_RESULTS_PER_QUERY = 3
MAX_RESULTS_PER_QUERY = 10

# Google reports quota exhaustion as HTTP 403, the same status as a rejected key;
# only these body reasons separate "come back tomorrow" from "fix the credential".
_QUOTA_REASONS = {"quotaExceeded", "rateLimitExceeded", "userRateLimitExceeded"}


class YouTubeProviderError(RuntimeError):
    """A YouTube provider request failed with a safe, machine-readable code."""

    def __init__(self, error_code: str, safe_message: str):
        super().__init__(safe_message)
        self.error_code = error_code
        self.safe_message = safe_message


class YouTubeProviderConfigurationError(YouTubeProviderError):
    """YouTube live configuration is missing or invalid."""


class YouTubeChannelSearchProvider(ABC):
    connector_name: str

    @abstractmethod
    def search(self, query_text: str, limit: int) -> dict[str, Any]:
        """Return one raw channel-list response without inferring creator quality."""


@dataclass(frozen=True, repr=False)
class YouTubeAPIConfiguration:
    api_key: str
    base_url: str = DEFAULT_YOUTUBE_API_BASE_URL
    timeout_seconds: int = 60

    def __post_init__(self) -> None:
        if not isinstance(self.api_key, str) or not self.api_key.strip():
            raise YouTubeProviderConfigurationError(
                "configuration_missing",
                "YOUTUBE_API_KEY is required for YouTube live retrieval",
            )
        if not isinstance(self.base_url, str) or not self.base_url.startswith("https://"):
            raise YouTubeProviderConfigurationError(
                "invalid_provider_configuration",
                "YOUTUBE_API_BASE_URL must be an HTTPS URL",
            )
        if not 10 <= self.timeout_seconds <= 180:
            raise YouTubeProviderConfigurationError(
                "invalid_provider_configuration",
                "YOUTUBE_API_TIMEOUT_SECONDS must be between 10 and 180",
            )

    @classmethod
    def from_environment(cls) -> "YouTubeAPIConfiguration":
        return cls(
            api_key=os.getenv("YOUTUBE_API_KEY", "").strip(),
            base_url=(
                os.getenv("YOUTUBE_API_BASE_URL", "").strip()
                or DEFAULT_YOUTUBE_API_BASE_URL
            ),
            timeout_seconds=_environment_int("YOUTUBE_API_TIMEOUT_SECONDS", 60),
        )


class YouTubeDataAPISearchProvider(YouTubeChannelSearchProvider):
    """Thin client for public channel search plus the channel resources it names.

    search.list returns only ids and a thin snippet, so the description and
    subscriber count need a second channels.list call on the same ids.
    """

    connector_name = "youtube_data_api_v3_search"

    def __init__(self, configuration: YouTubeAPIConfiguration):
        self.configuration = configuration

    def search(self, query_text: str, limit: int) -> dict[str, Any]:
        if not isinstance(query_text, str) or not query_text.strip():
            raise YouTubeProviderError("invalid_query", "approved query text must be non-empty")
        if not 1 <= limit <= MAX_RESULTS_PER_QUERY:
            raise YouTubeProviderError(
                "invalid_result_limit",
                f"result limit must be between 1 and {MAX_RESULTS_PER_QUERY}",
            )
        found = self._get(
            "/search",
            {
                "part": "snippet",
                "type": "channel",
                "q": query_text.strip(),
                "maxResults": limit,
            },
        )
        channel_ids = _channel_ids(found, limit)
        if not channel_ids:
            # An empty id list is an HTTP 400 from channels.list, so a zero-result
            # search must not spend the second request or its quota units.
            return {"items": []}
        return self._get(
            "/channels",
            {"part": "snippet,statistics", "id": ",".join(channel_ids)},
        )

    def _get(self, path: str, parameters: dict[str, Any]) -> dict[str, Any]:
        endpoint = (
            self.configuration.base_url.rstrip("/")
            + path
            + "?"
            + urlencode({**parameters, "key": self.configuration.api_key})
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
            raise YouTubeProviderError(
                "provider_timeout", "YouTube API request timed out"
            ) from exc
        except SSLError as exc:
            raise YouTubeProviderError(
                "provider_tls_failure", "YouTube API TLS certificate validation failed"
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, (TimeoutError, SocketTimeout)):
                code = "provider_timeout"
                message = "YouTube API request timed out"
            elif isinstance(exc.reason, (SSLCertVerificationError, SSLError)):
                code = "provider_tls_failure"
                message = "YouTube API TLS certificate validation failed"
            else:
                code = "provider_network_failure"
                message = "YouTube API request failed due to a network error"
            raise YouTubeProviderError(code, message) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise YouTubeProviderError(
                "malformed_provider_response", "YouTube API response was not valid JSON"
            ) from exc
        if not isinstance(data, dict):
            raise YouTubeProviderError(
                "malformed_provider_response", "YouTube API response must be an object"
            )
        return data

    @staticmethod
    def _http_error(exc: HTTPError) -> YouTubeProviderError:
        status = exc.code
        reasons = _http_error_reasons(exc)
        exc.close()
        if status in {401, 403} and reasons & _QUOTA_REASONS:
            return YouTubeProviderError(
                "provider_rate_limit_or_quota",
                "YouTube API quota or rate limit blocked the request",
            )
        if status in {401, 403}:
            return YouTubeProviderError(
                "provider_authentication_failure",
                "YouTube API rejected the credential or its permissions",
            )
        if status == 408:
            return YouTubeProviderError("provider_timeout", "YouTube API request timed out")
        if status == 429:
            return YouTubeProviderError(
                "provider_rate_limit_or_quota",
                "YouTube API quota or rate limit blocked the request",
            )
        return YouTubeProviderError(
            "provider_http_failure", f"YouTube API request failed with HTTP {status}"
        )


class YouTubeLiveRetrievalAdapter:
    """Map public YouTube channel results into the shared raw creator contract."""

    def __init__(
        self,
        provider: YouTubeChannelSearchProvider,
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
            raise TypeError("YouTube retrieval requires an ApprovedSearchPlan")
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("run_id must be a non-empty string")
        if query_limit is not None and query_limit < 1:
            raise ValueError("query_limit must be positive when provided")

        started_at = utc_now_iso()
        queries = [query for query in approved_plan.queries if query.platform == "youtube"]
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
        except YouTubeProviderError as exc:
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
                f"YouTube provider failed with {exc.__class__.__name__}",
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
                error_message="YouTube returned results, but none were valid creator records",
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
            raise YouTubeProviderError(
                "malformed_provider_response", "YouTube API response must be an object"
            )
        items = response.get("items")
        if items is None:
            if response.get("error"):
                raise YouTubeProviderError(
                    "provider_http_failure",
                    "YouTube API returned a structured provider error",
                )
            return [], [], 0
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise YouTubeProviderError(
                "malformed_provider_response",
                "YouTube API items must be an array of channels",
            )
        channels = items[: self.results_per_query]
        if not channels:
            if response.get("error"):
                raise YouTubeProviderError(
                    "provider_http_failure",
                    "YouTube API returned a structured provider error",
                )
            return [], [], 0

        retrieved_at = utc_now_iso()
        profiles: list[RawCreatorProfile] = []
        invalid_reasons: list[str] = []
        for index, channel in enumerate(channels):
            try:
                profiles.append(
                    self._map_profile(
                        channel,
                        approved_plan=approved_plan,
                        query=query,
                        run_id=run_id,
                        retrieved_at=retrieved_at,
                    )
                )
            except (TypeError, ValueError) as exc:
                invalid_reasons.append(
                    f"provider result {index} was not a valid YouTube creator: {exc}"
                )
        return profiles, invalid_reasons, len(channels)

    def _map_profile(
        self,
        channel: dict[str, Any],
        *,
        approved_plan: ApprovedSearchPlan,
        query: ApprovedSearchQuery,
        run_id: str,
        retrieved_at: str,
    ) -> RawCreatorProfile:
        channel_id = _required_text(channel.get("id"), "channel id")
        snippet = channel.get("snippet")
        if not isinstance(snippet, dict):
            raise ValueError("provider field snippet is missing")
        profile_url = _channel_profile_url(channel_id, snippet.get("customUrl"))
        signature = f"{run_id}|{query.query_id}|{profile_url}"
        return RawCreatorProfile(
            record_id=f"youtube_{sha256(signature.encode('utf-8')).hexdigest()[:16]}",
            platform="youtube",
            profile_url=profile_url,
            normalized_profile_url=normalize_profile_url(profile_url, "youtube"),
            display_name=_optional_text(snippet.get("title")),
            bio_text=_optional_text(snippet.get("description")),
            follower_count=_subscriber_count(channel.get("statistics")),
            # channels.list exposes no owner links, and inventing them would put
            # unobserved facts into an evidence record.
            external_urls=(),
            # Video text needs a per-channel playlist crawl; that cost and that
            # scraping surface stay out of the discovery pass on purpose.
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
            "platform": "youtube",
            "query_text": query.query_text,
            "search_angle": query.search_angle,
            "run_id": run_id,
        }


def _channel_ids(response: dict[str, Any], limit: int) -> list[str]:
    items = response.get("items")
    if items is None:
        return []
    if not isinstance(items, list):
        raise YouTubeProviderError(
            "malformed_provider_response", "YouTube search items must be an array"
        )
    ids: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            raise YouTubeProviderError(
                "malformed_provider_response", "YouTube search item must be an object"
            )
        snippet = item.get("snippet")
        candidate = snippet.get("channelId") if isinstance(snippet, dict) else None
        if not isinstance(candidate, str) or not candidate.strip():
            identifier = item.get("id")
            candidate = identifier.get("channelId") if isinstance(identifier, dict) else None
        if isinstance(candidate, str) and candidate.strip() and candidate.strip() not in ids:
            ids.append(candidate.strip())
        if len(ids) >= limit:
            break
    return ids


def _channel_profile_url(channel_id: str, custom_url: Any) -> str:
    """Prefer the public handle; fall back to the always-resolvable channel id."""

    if isinstance(custom_url, str):
        handle = custom_url.strip().lstrip("@")
        # A legacy customUrl can still carry a "c/" or "user/" prefix, which is a
        # path and not a handle; the channel id is the safe identity in that case.
        if handle and handle == "".join(handle.split()) and "/" not in handle:
            return f"https://www.youtube.com/@{handle}"
    return f"https://www.youtube.com/channel/{channel_id}"


def _http_error_reasons(exc: HTTPError) -> set[str]:
    """Read the Google error body, which is the only place quota reasons appear."""

    try:
        payload = json.loads(exc.read().decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return set()
    error = payload.get("error") if isinstance(payload, dict) else None
    entries = error.get("errors") if isinstance(error, dict) else None
    if not isinstance(entries, list):
        return set()
    return {
        entry["reason"]
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("reason"), str)
    }


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"provider field {field_name} is missing")
    return value.strip()


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _subscriber_count(statistics: Any) -> int | None:
    if not isinstance(statistics, dict):
        return None
    # A hidden count is a deliberate creator choice, not a zero.
    if statistics.get("hiddenSubscriberCount") is True:
        return None
    raw = statistics.get("subscriberCount")
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw if raw >= 0 else None
    # The API serializes counts as decimal strings.
    if isinstance(raw, str) and raw.strip().isdecimal():
        return int(raw.strip())
    return None


def _environment_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise YouTubeProviderConfigurationError(
            "invalid_provider_configuration", f"{name} must be an integer"
        ) from exc
