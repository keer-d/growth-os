"""Approved Instagram query retrieval through a public-data provider."""

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
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from domain.models import ContentSample, RawCreatorProfile, utc_now_iso
from domain.query_review import ApprovedSearchPlan, ApprovedSearchQuery
from domain.retrieval import (
    InstagramQueryRetrievalResult,
    InstagramRetrievalRunResult,
)
from pipeline.normalize import normalize_profile_url
from pipeline.tls import trusted_ssl_context


DEFAULT_APIFY_ACTOR_ID = "apify~instagram-search-scraper"
DEFAULT_RESULTS_PER_QUERY = 3
MAX_RESULTS_PER_QUERY = 10


class InstagramProviderError(RuntimeError):
    """A provider request failed with a safe, machine-readable code."""

    def __init__(self, error_code: str, safe_message: str):
        super().__init__(safe_message)
        self.error_code = error_code
        self.safe_message = safe_message


class InstagramProviderConfigurationError(InstagramProviderError):
    """Live provider configuration is missing or invalid."""


class InstagramProfileSearchProvider(ABC):
    connector_name: str

    @abstractmethod
    def search_profiles(self, query_text: str, limit: int) -> list[dict[str, Any]]:
        """Return observable public profile results for one approved query."""


@dataclass(frozen=True, repr=False)
class ApifyInstagramConfiguration:
    api_token: str
    actor_id: str = DEFAULT_APIFY_ACTOR_ID
    timeout_seconds: int = 180
    max_total_charge_usd: float = 0.25

    def __post_init__(self) -> None:
        if not isinstance(self.api_token, str) or not self.api_token.strip():
            raise InstagramProviderConfigurationError(
                "missing_api_credential",
                "APIFY_API_TOKEN is required for Instagram live retrieval",
            )
        if not isinstance(self.actor_id, str) or not self.actor_id.strip():
            raise InstagramProviderConfigurationError(
                "invalid_provider_configuration",
                "APIFY_INSTAGRAM_ACTOR_ID must be a non-empty Actor ID",
            )
        if not 30 <= self.timeout_seconds <= 300:
            raise InstagramProviderConfigurationError(
                "invalid_provider_configuration",
                "APIFY_INSTAGRAM_TIMEOUT_SECONDS must be between 30 and 300",
            )
        if not 0 < self.max_total_charge_usd <= 5:
            raise InstagramProviderConfigurationError(
                "invalid_provider_configuration",
                "APIFY_INSTAGRAM_MAX_TOTAL_CHARGE_USD must be greater than 0 and at most 5",
            )

    @classmethod
    def from_environment(cls) -> "ApifyInstagramConfiguration":
        token = os.getenv("APIFY_API_TOKEN", "").strip()
        actor_id = (
            os.getenv("APIFY_INSTAGRAM_ACTOR_ID", "").strip()
            or DEFAULT_APIFY_ACTOR_ID
        )
        timeout_seconds = _environment_int("APIFY_INSTAGRAM_TIMEOUT_SECONDS", 180)
        max_charge = _environment_float("APIFY_INSTAGRAM_MAX_TOTAL_CHARGE_USD", 0.25)
        return cls(
            api_token=token,
            actor_id=actor_id,
            timeout_seconds=timeout_seconds,
            max_total_charge_usd=max_charge,
        )


class ApifyInstagramSearchProvider(InstagramProfileSearchProvider):
    """Thin Apify Actor API client; credentials never enter URLs or output."""

    connector_name = "apify_instagram_search_scraper"

    def __init__(self, configuration: ApifyInstagramConfiguration):
        self.configuration = configuration

    def search_profiles(self, query_text: str, limit: int) -> list[dict[str, Any]]:
        if not isinstance(query_text, str) or not query_text.strip():
            raise InstagramProviderError(
                "invalid_query", "approved query text must be non-empty"
            )
        if not 1 <= limit <= MAX_RESULTS_PER_QUERY:
            raise InstagramProviderError(
                "invalid_result_limit",
                f"result limit must be between 1 and {MAX_RESULTS_PER_QUERY}",
            )

        actor_id = quote(self.configuration.actor_id, safe="~")
        actor_timeout = min(self.configuration.timeout_seconds, 300)
        parameters = urlencode(
            {
                "timeout": actor_timeout,
                "maxItems": limit,
                "maxTotalChargeUsd": self.configuration.max_total_charge_usd,
                "format": "json",
                "clean": "true",
                "limit": limit,
            }
        )
        endpoint = (
            f"https://api.apify.com/v2/actors/{actor_id}/"
            f"run-sync-get-dataset-items?{parameters}"
        )
        payload = {
            "search": query_text.strip(),
            "searchType": "user",
            "searchLimit": limit,
            "enhanceUserSearchWithFacebookPage": False,
        }
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.configuration.api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(
                request,
                timeout=self.configuration.timeout_seconds + 10,
                context=trusted_ssl_context(),
            ) as response:
                body = response.read().decode("utf-8")
            data = json.loads(body)
        except HTTPError as exc:
            raise self._http_error(exc) from exc
        except (TimeoutError, SocketTimeout) as exc:
            raise InstagramProviderError(
                "provider_timeout", "Apify Instagram request timed out"
            ) from exc
        except SSLError as exc:
            raise InstagramProviderError(
                "provider_tls_failure",
                "Apify Instagram TLS certificate validation failed",
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, (TimeoutError, SocketTimeout)):
                code = "provider_timeout"
                message = "Apify Instagram request timed out"
            elif isinstance(exc.reason, (SSLCertVerificationError, SSLError)):
                code = "provider_tls_failure"
                message = "Apify Instagram TLS certificate validation failed"
            else:
                code = "provider_network_failure"
                message = "Apify Instagram request failed due to a network error"
            raise InstagramProviderError(code, message) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InstagramProviderError(
                "malformed_provider_response",
                "Apify Instagram response was not valid JSON",
            ) from exc

        if (
            isinstance(data, list)
            and len(data) == 1
            and isinstance(data[0], dict)
            and data[0].get("error")
        ):
            if data[0].get("error") == "no_items":
                return []
            raise InstagramProviderError(
                "provider_http_failure",
                "Apify Instagram Actor returned a structured provider error",
            )

        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise InstagramProviderError(
                "malformed_provider_response",
                "Apify Instagram response must be an array of objects",
            )
        return data

    @staticmethod
    def _http_error(exc: HTTPError) -> InstagramProviderError:
        body = ""
        try:
            body = exc.read(4096).decode("utf-8", errors="replace")
        except Exception:
            body = ""
        finally:
            exc.close()
        error_type = ""
        provider_message = ""
        try:
            error = json.loads(body).get("error", {})
            if isinstance(error, dict):
                error_type = str(error.get("type") or "")
                provider_message = str(error.get("message") or "")
        except (json.JSONDecodeError, AttributeError):
            pass

        searchable = f"{error_type} {provider_message}".casefold()
        if exc.code in {401, 403}:
            code = "provider_authentication_failure"
            message = "Apify rejected the API credential or its permissions"
        elif exc.code == 408 or "timeout" in searchable:
            code = "provider_timeout"
            message = "Apify Instagram Actor exceeded the request timeout"
        elif exc.code in {402, 429} or any(
            term in searchable
            for term in (
                "rate-limit",
                "usage-limit",
                "not-enough-usage",
                "limit-reached",
                "charge",
                "quota",
                "payment-required",
            )
        ):
            code = "provider_rate_limit_or_quota"
            message = "Apify rate limit, quota, or spending cap blocked the request"
        else:
            code = "provider_http_failure"
            message = f"Apify Instagram request failed with HTTP {exc.code}"
        return InstagramProviderError(code, message)


class InstagramLiveRetrievalAdapter:
    """Execute only approved Instagram queries and map them into Raw profiles."""

    def __init__(
        self,
        provider: InstagramProfileSearchProvider,
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
    ) -> InstagramRetrievalRunResult:
        if not isinstance(approved_plan, ApprovedSearchPlan) or approved_plan.status != "approved":
            raise TypeError("Instagram retrieval requires an ApprovedSearchPlan")
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("run_id must be a non-empty string")
        if query_limit is not None and query_limit < 1:
            raise ValueError("query_limit must be positive when provided")

        queries = [query for query in approved_plan.queries if query.platform == "instagram"]
        if query_limit is not None:
            queries = queries[:query_limit]
        results = tuple(
            self._retrieve_query(approved_plan, query, run_id.strip()) for query in queries
        )
        return InstagramRetrievalRunResult(
            run_id=run_id.strip(),
            campaign_id=approved_plan.campaign_id,
            approved_search_plan_id=approved_plan.approved_search_plan_id,
            discovery_mode="live_instagram",
            query_results=results,
        )

    def _retrieve_query(
        self,
        approved_plan: ApprovedSearchPlan,
        query: ApprovedSearchQuery,
        run_id: str,
    ) -> InstagramQueryRetrievalResult:
        started_at = utc_now_iso()
        try:
            provider_rows = self.provider.search_profiles(
                query.query_text, self.results_per_query
            )
            if not isinstance(provider_rows, list):
                raise InstagramProviderError(
                    "malformed_provider_response",
                    "Instagram provider response must be an array",
                )
        except InstagramProviderError as exc:
            return self._failure_result(
                approved_plan, query, run_id, started_at, exc.error_code, exc.safe_message
            )
        except Exception as exc:
            return self._failure_result(
                approved_plan,
                query,
                run_id,
                started_at,
                "unexpected_provider_failure",
                f"Instagram provider failed with {exc.__class__.__name__}",
            )

        retrieved_at = utc_now_iso()
        profiles = []
        invalid_reasons = []
        for index, row in enumerate(provider_rows):
            try:
                profiles.append(
                    self._map_profile(
                        row,
                        approved_plan=approved_plan,
                        query=query,
                        run_id=run_id,
                        retrieved_at=retrieved_at,
                    )
                )
            except (TypeError, ValueError) as exc:
                invalid_reasons.append(
                    f"provider result {index} was not a valid Instagram profile: {exc}"
                )

        if provider_rows and not profiles:
            return InstagramQueryRetrievalResult(
                campaign_id=approved_plan.campaign_id,
                approved_search_plan_id=approved_plan.approved_search_plan_id,
                query_id=query.query_id,
                source_query_id=query.source_query_id,
                query_text=query.query_text,
                search_angle=query.search_angle,
                run_id=run_id,
                status="failed",
                profiles=(),
                provider_result_count=len(provider_rows),
                invalid_result_count=len(invalid_reasons),
                invalid_result_reasons=tuple(invalid_reasons),
                started_at=started_at,
                completed_at=retrieved_at,
                error_code="invalid_creator_record",
                error_message="Provider returned results, but none were valid profile records",
            )
        return InstagramQueryRetrievalResult(
            campaign_id=approved_plan.campaign_id,
            approved_search_plan_id=approved_plan.approved_search_plan_id,
            query_id=query.query_id,
            source_query_id=query.source_query_id,
            query_text=query.query_text,
            search_angle=query.search_angle,
            run_id=run_id,
            status="succeeded",
            profiles=tuple(profiles),
            provider_result_count=len(provider_rows),
            invalid_result_count=len(invalid_reasons),
            invalid_result_reasons=tuple(invalid_reasons),
            started_at=started_at,
            completed_at=retrieved_at,
        )

    def _failure_result(
        self,
        approved_plan: ApprovedSearchPlan,
        query: ApprovedSearchQuery,
        run_id: str,
        started_at: str,
        error_code: str,
        error_message: str,
    ) -> InstagramQueryRetrievalResult:
        return InstagramQueryRetrievalResult(
            campaign_id=approved_plan.campaign_id,
            approved_search_plan_id=approved_plan.approved_search_plan_id,
            query_id=query.query_id,
            source_query_id=query.source_query_id,
            query_text=query.query_text,
            search_angle=query.search_angle,
            run_id=run_id,
            status="failed",
            profiles=(),
            provider_result_count=0,
            invalid_result_count=0,
            invalid_result_reasons=(),
            started_at=started_at,
            completed_at=utc_now_iso(),
            error_code=error_code,
            error_message=error_message,
        )

    def _map_profile(
        self,
        row: Any,
        *,
        approved_plan: ApprovedSearchPlan,
        query: ApprovedSearchQuery,
        run_id: str,
        retrieved_at: str,
    ) -> RawCreatorProfile:
        if not isinstance(row, dict):
            raise TypeError("result must be an object")
        profile_url = _required_provider_text(
            row.get("url") or row.get("profileUrl"), "url"
        )
        normalized_profile_url = normalize_profile_url(profile_url, "instagram")
        record_signature = f"{run_id}|{query.query_id}|{profile_url}"
        record_id = f"ig_{sha256(record_signature.encode('utf-8')).hexdigest()[:16]}"
        return RawCreatorProfile(
            record_id=record_id,
            platform="instagram",
            profile_url=profile_url,
            normalized_profile_url=normalized_profile_url,
            display_name=_optional_provider_text(row.get("fullName")),
            bio_text=_optional_provider_text(row.get("biography")),
            follower_count=_optional_nonnegative_int(row.get("followersCount")),
            external_urls=_external_urls(row),
            content_samples=_content_samples(row),
            discovery_mode="live_instagram",
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


def _required_provider_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"provider field {field_name} is missing")
    return value.strip()


def _optional_provider_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _optional_nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _external_urls(row: dict[str, Any]) -> tuple[str, ...]:
    urls = []
    candidates = row.get("externalUrls")
    if isinstance(candidates, list):
        for item in candidates:
            value = item.get("url") if isinstance(item, dict) else item
            if isinstance(value, str) and value.strip() and value.strip() not in urls:
                urls.append(value.strip())
    single = row.get("externalUrl")
    if isinstance(single, str) and single.strip() and single.strip() not in urls:
        urls.append(single.strip())
    return tuple(urls)


def _content_samples(row: dict[str, Any]) -> tuple[ContentSample, ...]:
    samples = []
    for field_name in ("latestPosts", "latestIgtvVideos"):
        items = row.get(field_name)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            text = _optional_provider_text(item.get("caption"))
            if text is None:
                continue
            samples.append(
                ContentSample(
                    text=text,
                    url=_optional_provider_text(item.get("url")),
                    published_at=_optional_provider_text(item.get("timestamp")),
                )
            )
            if len(samples) == 5:
                return tuple(samples)
    return tuple(samples)


def _environment_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise InstagramProviderConfigurationError(
            "invalid_provider_configuration", f"{name} must be an integer"
        ) from exc


def _environment_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise InstagramProviderConfigurationError(
            "invalid_provider_configuration", f"{name} must be numeric"
        ) from exc
