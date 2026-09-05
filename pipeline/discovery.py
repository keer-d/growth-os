"""Unified controlled/live execution of human-approved creator queries."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
import logging
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from domain.query_review import ApprovedSearchPlan, ApprovedSearchQuery
from domain.retrieval import (
    DiscoveryQueryResult,
    DiscoveryRunResult,
    InstagramQueryRetrievalResult,
)
from domain.models import RawCreatorProfile, utc_now_iso
from pipeline.instagram_retrieval import (
    ApifyInstagramConfiguration,
    ApifyInstagramSearchProvider,
    InstagramLiveRetrievalAdapter,
    InstagramProviderConfigurationError,
)
from pipeline.read_creators import load_creators
from pipeline.web_retrieval import (
    WebLiveRetrievalAdapter,
    WebProviderConfigurationError,
    WebSearchAPIProvider,
    WebSearchConfiguration,
)
from pipeline.x_retrieval import (
    XAPIConfiguration,
    XLiveRetrievalAdapter,
    XProviderConfigurationError,
    XRecentSearchProvider,
)
from pipeline.youtube_retrieval import (
    YouTubeAPIConfiguration,
    YouTubeDataAPISearchProvider,
    YouTubeLiveRetrievalAdapter,
    YouTubeProviderConfigurationError,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTROLLED_FIXTURE = PROJECT_ROOT / "fixtures" / "controlled_demo_minimal.json"
LOGGER = logging.getLogger("creator_discovery.run")
_AUTO = object()

# A skipped or failed channel never reaches its provider, so the connector it
# *would* have used has to be named here for the row to stay auditable.
_CHANNEL_CONNECTOR: dict[str, str] = {
    "instagram": "apify_instagram_search_scraper",
    "x": "x_api_v2_recent_search",
    "youtube": "youtube_data_api_v3_search",
    "web": "web_search_api_v1",
}


class ControlledFixtureRetrievalAdapter:
    """Offline adapter that assigns curated public snapshots only to approved queries."""

    connector_name = "curated_public_fixture_v1"

    def __init__(self, fixture_path: str | Path = DEFAULT_CONTROLLED_FIXTURE):
        self.fixture_path = Path(fixture_path)

    def retrieve(
        self, approved_plan: ApprovedSearchPlan, *, run_id: str
    ) -> DiscoveryRunResult:
        _require_approved_plan(approved_plan)
        started_at = utc_now_iso()
        fixture_profiles = load_creators(self.fixture_path)
        buckets: dict[str, list[RawCreatorProfile]] = {
            query.query_id: [] for query in approved_plan.queries
        }
        # Only the channels the human actually approved. The fixture carries
        # instagram and x records only, so a youtube or web query finds no
        # matching profiles, keeps an empty bucket, and reports a truthful
        # SUCCESS_ZERO_RESULTS instead of borrowing another channel's records.
        for platform in dict.fromkeys(query.platform for query in approved_plan.queries):
            queries = [query for query in approved_plan.queries if query.platform == platform]
            platform_profiles = [
                profile for profile in fixture_profiles if profile.platform == platform
            ]
            for index, profile in enumerate(platform_profiles):
                query = queries[index % len(queries)]
                buckets[query.query_id].append(
                    self._rebase_profile(profile, approved_plan, query, run_id)
                )

        results = tuple(
            self._query_result(approved_plan, query, run_id, buckets[query.query_id])
            for query in approved_plan.queries
        )
        return DiscoveryRunResult(
            run_id=run_id,
            campaign_id=approved_plan.campaign_id,
            approved_search_plan_id=approved_plan.approved_search_plan_id,
            discovery_mode="controlled",
            query_results=results,
            started_at=started_at,
            completed_at=utc_now_iso(),
        )

    def _rebase_profile(
        self,
        profile: RawCreatorProfile,
        approved_plan: ApprovedSearchPlan,
        query: ApprovedSearchQuery,
        run_id: str,
    ) -> RawCreatorProfile:
        signature = f"{run_id}|{query.query_id}|{profile.record_id}"
        return replace(
            profile,
            record_id=f"demo_{sha256(signature.encode('utf-8')).hexdigest()[:16]}",
            discovery_mode="controlled_demo",
            source_connector=self.connector_name,
            run_id=run_id,
            query_id=query.query_id,
            retrieved_at=utc_now_iso(),
            campaign_id=approved_plan.campaign_id,
            approved_search_plan_id=approved_plan.approved_search_plan_id,
            source_query_id=query.source_query_id,
            query_text=query.query_text,
            search_angle=query.search_angle,
        )

    def _query_result(
        self,
        approved_plan: ApprovedSearchPlan,
        query: ApprovedSearchQuery,
        run_id: str,
        profiles: list[RawCreatorProfile],
    ) -> DiscoveryQueryResult:
        timestamp = utc_now_iso()
        return DiscoveryQueryResult(
            campaign_id=approved_plan.campaign_id,
            approved_search_plan_id=approved_plan.approved_search_plan_id,
            query_id=query.query_id,
            source_query_id=query.source_query_id,
            platform=query.platform,
            query_text=query.query_text,
            search_angle=query.search_angle,
            run_id=run_id,
            source_connector=self.connector_name,
            status="SUCCESS_WITH_RESULTS" if profiles else "SUCCESS_ZERO_RESULTS",
            profiles=tuple(profiles),
            provider_result_count=len(profiles),
            invalid_result_count=0,
            invalid_result_reasons=(),
            started_at=timestamp,
            completed_at=timestamp,
        )


class UnifiedDiscoveryRunner:
    """Route approved queries while preserving per-query provider outcomes."""

    def __init__(
        self,
        *,
        controlled_adapter: ControlledFixtureRetrievalAdapter | None = None,
        instagram_adapter: InstagramLiveRetrievalAdapter | None | object = _AUTO,
        x_adapter: XLiveRetrievalAdapter | None | object = _AUTO,
        youtube_adapter: YouTubeLiveRetrievalAdapter | None | object = _AUTO,
        web_adapter: WebLiveRetrievalAdapter | None | object = _AUTO,
        logger: logging.Logger | None = None,
    ):
        self.controlled_adapter = controlled_adapter or ControlledFixtureRetrievalAdapter()
        self.instagram_adapter = instagram_adapter
        self.x_adapter = x_adapter
        self.youtube_adapter = youtube_adapter
        self.web_adapter = web_adapter
        self.logger = logger or LOGGER

    def run(
        self,
        approved_plan: ApprovedSearchPlan,
        *,
        mode: str,
        run_id: str | None = None,
    ) -> DiscoveryRunResult:
        _require_approved_plan(approved_plan)
        if mode not in {"controlled", "live"}:
            raise ValueError("mode must be controlled or live")
        run_id = run_id or f"discovery_{uuid4().hex[:16]}"
        started_at = utc_now_iso()
        self._log(
            "run_started",
            run_id=run_id,
            campaign_id=approved_plan.campaign_id,
            mode=mode,
            approved_query_count=len(approved_plan.queries),
        )

        if mode == "controlled":
            result = self.controlled_adapter.retrieve(approved_plan, run_id=run_id)
        else:
            result = self._run_live(approved_plan, run_id, started_at)

        for query_result in result.query_results:
            self._log(
                "query_completed",
                run_id=run_id,
                query_id=query_result.query_id,
                platform=query_result.platform,
                provider=query_result.source_connector,
                status=query_result.status,
                retrieved=query_result.retrieved_count,
                invalid=query_result.invalid_result_count,
                error_code=query_result.error_code,
                duration_seconds=query_result.duration_seconds,
            )
        self._log(
            "run_retrieval_completed",
            run_id=run_id,
            query_count=len(result.query_results),
            retrieved=len(result.profiles),
            failed=sum(item.status == "FAILED" for item in result.query_results),
            skipped=sum(
                item.status == "SKIPPED_NOT_CONFIGURED" for item in result.query_results
            ),
        )
        return result

    def _run_live(
        self,
        approved_plan: ApprovedSearchPlan,
        run_id: str,
        started_at: str,
    ) -> DiscoveryRunResult:
        results: list[DiscoveryQueryResult] = []
        instagram_adapter, instagram_error = self._instagram_live_adapter()
        if instagram_adapter is None:
            results.extend(
                self._unavailable_results(
                    approved_plan,
                    platform="instagram",
                    run_id=run_id,
                    error=instagram_error,
                )
            )
        else:
            instagram_run = instagram_adapter.retrieve(approved_plan, run_id=run_id)
            results.extend(
                self._instagram_result(instagram_adapter, item)
                for item in instagram_run.query_results
            )

        x_adapter, x_error = self._x_live_adapter()
        if x_adapter is None:
            results.extend(
                self._unavailable_results(
                    approved_plan,
                    platform="x",
                    run_id=run_id,
                    error=x_error,
                )
            )
        else:
            x_run = x_adapter.retrieve(approved_plan, run_id=run_id)
            results.extend(x_run.query_results)

        youtube_adapter, youtube_error = self._youtube_live_adapter()
        if youtube_adapter is None:
            results.extend(
                self._unavailable_results(
                    approved_plan,
                    platform="youtube",
                    run_id=run_id,
                    error=youtube_error,
                )
            )
        else:
            youtube_run = youtube_adapter.retrieve(approved_plan, run_id=run_id)
            results.extend(youtube_run.query_results)

        web_adapter, web_error = self._web_live_adapter()
        if web_adapter is None:
            results.extend(
                self._unavailable_results(
                    approved_plan,
                    platform="web",
                    run_id=run_id,
                    error=web_error,
                )
            )
        else:
            web_run = web_adapter.retrieve(approved_plan, run_id=run_id)
            results.extend(web_run.query_results)

        # An unconfigured channel the plan never asked for contributes nothing:
        # both the adapters and _unavailable_results filter on query.platform.
        by_query = {result.query_id: result for result in results}
        ordered = tuple(by_query[query.query_id] for query in approved_plan.queries)
        return DiscoveryRunResult(
            run_id=run_id,
            campaign_id=approved_plan.campaign_id,
            approved_search_plan_id=approved_plan.approved_search_plan_id,
            discovery_mode="live",
            query_results=ordered,
            started_at=started_at,
            completed_at=utc_now_iso(),
        )

    def _instagram_live_adapter(
        self,
    ) -> tuple[InstagramLiveRetrievalAdapter | None, tuple[str, str] | None]:
        if self.instagram_adapter is not _AUTO:
            return self.instagram_adapter, (
                None
                if self.instagram_adapter is not None
                else ("configuration_missing", "Instagram provider is not configured")
            )
        try:
            configuration = ApifyInstagramConfiguration.from_environment()
            limit = _environment_result_limit(
                "APIFY_INSTAGRAM_RESULTS_LIMIT",
                3,
                InstagramProviderConfigurationError,
            )
            return (
                InstagramLiveRetrievalAdapter(
                    ApifyInstagramSearchProvider(configuration),
                    results_per_query=limit,
                ),
                None,
            )
        except InstagramProviderConfigurationError as exc:
            code = (
                "configuration_missing"
                if exc.error_code == "missing_api_credential"
                else exc.error_code
            )
            return None, (code, exc.safe_message)

    def _x_live_adapter(
        self,
    ) -> tuple[XLiveRetrievalAdapter | None, tuple[str, str] | None]:
        if self.x_adapter is not _AUTO:
            return self.x_adapter, (
                None
                if self.x_adapter is not None
                else ("configuration_missing", "X provider is not configured")
            )
        try:
            configuration = XAPIConfiguration.from_environment()
            limit = _environment_result_limit(
                "X_RESULTS_PER_QUERY", 3, XProviderConfigurationError
            )
            return (
                XLiveRetrievalAdapter(
                    XRecentSearchProvider(configuration), results_per_query=limit
                ),
                None,
            )
        except XProviderConfigurationError as exc:
            return None, (exc.error_code, exc.safe_message)

    def _youtube_live_adapter(
        self,
    ) -> tuple[YouTubeLiveRetrievalAdapter | None, tuple[str, str] | None]:
        if self.youtube_adapter is not _AUTO:
            return self.youtube_adapter, (
                None
                if self.youtube_adapter is not None
                else ("configuration_missing", "YouTube provider is not configured")
            )
        try:
            configuration = YouTubeAPIConfiguration.from_environment()
            limit = _environment_result_limit(
                "YOUTUBE_RESULTS_PER_QUERY", 3, YouTubeProviderConfigurationError
            )
            return (
                YouTubeLiveRetrievalAdapter(
                    YouTubeDataAPISearchProvider(configuration),
                    results_per_query=limit,
                ),
                None,
            )
        except YouTubeProviderConfigurationError as exc:
            return None, (exc.error_code, exc.safe_message)

    def _web_live_adapter(
        self,
    ) -> tuple[WebLiveRetrievalAdapter | None, tuple[str, str] | None]:
        if self.web_adapter is not _AUTO:
            return self.web_adapter, (
                None
                if self.web_adapter is not None
                else ("configuration_missing", "Web provider is not configured")
            )
        try:
            configuration = WebSearchConfiguration.from_environment()
            limit = _environment_result_limit(
                "WEB_RESULTS_PER_QUERY", 3, WebProviderConfigurationError
            )
            return (
                WebLiveRetrievalAdapter(
                    WebSearchAPIProvider(configuration), results_per_query=limit
                ),
                None,
            )
        except WebProviderConfigurationError as exc:
            return None, (exc.error_code, exc.safe_message)

    @staticmethod
    def _instagram_result(
        adapter: InstagramLiveRetrievalAdapter,
        result: InstagramQueryRetrievalResult,
    ) -> DiscoveryQueryResult:
        if result.status == "succeeded":
            status = "SUCCESS_WITH_RESULTS" if result.profiles else "SUCCESS_ZERO_RESULTS"
        else:
            status = "FAILED"
        return DiscoveryQueryResult(
            campaign_id=result.campaign_id,
            approved_search_plan_id=result.approved_search_plan_id,
            query_id=result.query_id,
            source_query_id=result.source_query_id,
            platform="instagram",
            query_text=result.query_text,
            search_angle=result.search_angle,
            run_id=result.run_id,
            source_connector=adapter.provider.connector_name,
            status=status,
            profiles=result.profiles,
            provider_result_count=result.provider_result_count,
            invalid_result_count=result.invalid_result_count,
            invalid_result_reasons=result.invalid_result_reasons,
            started_at=result.started_at,
            completed_at=result.completed_at,
            error_code=result.error_code,
            error_message=result.error_message,
        )

    @staticmethod
    def _unavailable_results(
        approved_plan: ApprovedSearchPlan,
        *,
        platform: str,
        run_id: str,
        error: tuple[str, str] | None,
    ) -> list[DiscoveryQueryResult]:
        error_code, error_message = error or (
            "configuration_missing",
            f"{platform} provider is not configured",
        )
        status = (
            "SKIPPED_NOT_CONFIGURED"
            if error_code == "configuration_missing"
            else "FAILED"
        )
        timestamp = utc_now_iso()
        return [
            DiscoveryQueryResult(
                campaign_id=approved_plan.campaign_id,
                approved_search_plan_id=approved_plan.approved_search_plan_id,
                query_id=query.query_id,
                source_query_id=query.source_query_id,
                platform=platform,
                query_text=query.query_text,
                search_angle=query.search_angle,
                run_id=run_id,
                source_connector=_CHANNEL_CONNECTOR[platform],
                status=status,
                profiles=(),
                provider_result_count=0,
                invalid_result_count=0,
                invalid_result_reasons=(),
                started_at=timestamp,
                completed_at=timestamp,
                error_code=error_code,
                error_message=error_message,
            )
            for query in approved_plan.queries
            if query.platform == platform
        ]

    def _log(self, event: str, **fields: Any) -> None:
        payload = {"event": event, **fields}
        self.logger.info(json.dumps(payload, sort_keys=True, default=str))


def _require_approved_plan(value: ApprovedSearchPlan) -> None:
    if not isinstance(value, ApprovedSearchPlan) or value.status != "approved":
        raise TypeError("discovery requires an ApprovedSearchPlan")


def _environment_result_limit(name: str, default: int, error_type) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise error_type(
            "invalid_provider_configuration", f"{name} must be an integer"
        ) from exc
    if not 1 <= value <= 10:
        raise error_type(
            "invalid_provider_configuration", f"{name} must be between 1 and 10"
        )
    return value
