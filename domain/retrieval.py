"""Structured outcomes for approved-query creator retrieval."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from domain.models import PLATFORMS, RawCreatorProfile


RETRIEVAL_STATUSES = {"succeeded", "failed"}
QUERY_EXECUTION_STATUSES = {
    "SUCCESS_WITH_RESULTS",
    "SUCCESS_ZERO_RESULTS",
    "FAILED",
    "SKIPPED_NOT_CONFIGURED",
}
DISCOVERY_RUN_MODES = {"controlled", "live"}


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class InstagramQueryRetrievalResult:
    """Success or failure for one approved Instagram query."""

    campaign_id: str
    approved_search_plan_id: str
    query_id: str
    source_query_id: str
    query_text: str
    search_angle: str
    run_id: str
    status: str
    profiles: tuple[RawCreatorProfile, ...]
    provider_result_count: int
    invalid_result_count: int
    invalid_result_reasons: tuple[str, ...]
    started_at: str
    completed_at: str
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "campaign_id",
            "approved_search_plan_id",
            "query_id",
            "source_query_id",
            "query_text",
            "search_angle",
            "run_id",
            "started_at",
            "completed_at",
        ):
            _required_text(getattr(self, field_name), field_name)
        if self.status not in RETRIEVAL_STATUSES:
            raise ValueError(f"status must be one of {sorted(RETRIEVAL_STATUSES)}")
        if self.provider_result_count < 0 or self.invalid_result_count < 0:
            raise ValueError("retrieval counts cannot be negative")
        if self.invalid_result_count > self.provider_result_count:
            raise ValueError("invalid_result_count cannot exceed provider_result_count")
        if self.invalid_result_count != len(self.invalid_result_reasons):
            raise ValueError("each invalid provider result must have one reason")
        if len(self.profiles) + self.invalid_result_count != self.provider_result_count:
            raise ValueError("valid and invalid results must reconcile to provider_result_count")
        if self.status == "succeeded":
            if self.error_code is not None or self.error_message is not None:
                raise ValueError("successful retrieval cannot contain an error")
        else:
            _required_text(self.error_code, "error_code")
            _required_text(self.error_message, "error_message")
            if self.profiles:
                raise ValueError("failed retrieval cannot contain mapped profiles")
        if any(profile.query_id != self.query_id for profile in self.profiles):
            raise ValueError("every profile must reference the retrieval query_id")
        if any(profile.run_id != self.run_id for profile in self.profiles):
            raise ValueError("every profile must reference the retrieval run_id")
        if any(profile.campaign_id != self.campaign_id for profile in self.profiles):
            raise ValueError("every profile must reference the retrieval campaign_id")
        if any(
            profile.approved_search_plan_id != self.approved_search_plan_id
            for profile in self.profiles
        ):
            raise ValueError("every profile must reference the Approved Search Plan")
        if any(profile.source_query_id != self.source_query_id for profile in self.profiles):
            raise ValueError("every profile must reference the source Draft query")
        if any(profile.query_text != self.query_text for profile in self.profiles):
            raise ValueError("every profile must preserve the final approved query text")
        if any(profile.search_angle != self.search_angle for profile in self.profiles):
            raise ValueError("every profile must preserve the approved search angle")

    @property
    def valid_result_count(self) -> int:
        return len(self.profiles)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InstagramRetrievalRunResult:
    """All approved Instagram query outcomes from one bounded run."""

    run_id: str
    campaign_id: str
    approved_search_plan_id: str
    discovery_mode: str
    query_results: tuple[InstagramQueryRetrievalResult, ...]

    def __post_init__(self) -> None:
        for field_name in ("run_id", "campaign_id", "approved_search_plan_id"):
            _required_text(getattr(self, field_name), field_name)
        if self.discovery_mode != "live_instagram":
            raise ValueError("Instagram live retrieval mode must be live_instagram")
        query_ids = [result.query_id for result in self.query_results]
        if len(query_ids) != len(set(query_ids)):
            raise ValueError("each approved query can have only one retrieval result")
        if any(result.run_id != self.run_id for result in self.query_results):
            raise ValueError("every query result must reference the retrieval run_id")
        if any(result.campaign_id != self.campaign_id for result in self.query_results):
            raise ValueError("every query result must reference the retrieval campaign_id")
        if any(
            result.approved_search_plan_id != self.approved_search_plan_id
            for result in self.query_results
        ):
            raise ValueError("every query result must reference the Approved Search Plan")

    @property
    def profiles(self) -> tuple[RawCreatorProfile, ...]:
        return tuple(
            profile
            for result in self.query_results
            for profile in result.profiles
        )

    @property
    def succeeded_query_count(self) -> int:
        return sum(result.status == "succeeded" for result in self.query_results)

    @property
    def failed_query_count(self) -> int:
        return sum(result.status == "failed" for result in self.query_results)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiscoveryQueryResult:
    """Provider-neutral outcome for one approved query execution."""

    campaign_id: str
    approved_search_plan_id: str
    query_id: str
    source_query_id: str
    platform: str
    query_text: str
    search_angle: str
    run_id: str
    source_connector: str
    status: str
    profiles: tuple[RawCreatorProfile, ...]
    provider_result_count: int
    invalid_result_count: int
    invalid_result_reasons: tuple[str, ...]
    started_at: str
    completed_at: str
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "campaign_id",
            "approved_search_plan_id",
            "query_id",
            "source_query_id",
            "platform",
            "query_text",
            "search_angle",
            "run_id",
            "source_connector",
            "started_at",
            "completed_at",
        ):
            _required_text(getattr(self, field_name), field_name)
        if self.platform not in PLATFORMS:
            raise ValueError(f"platform must be one of {sorted(PLATFORMS)}")
        if self.status not in QUERY_EXECUTION_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(QUERY_EXECUTION_STATUSES)}"
            )
        if self.provider_result_count < 0 or self.invalid_result_count < 0:
            raise ValueError("retrieval counts cannot be negative")
        if self.invalid_result_count > self.provider_result_count:
            raise ValueError("invalid_result_count cannot exceed provider_result_count")
        if len(self.invalid_result_reasons) != self.invalid_result_count:
            raise ValueError("each invalid provider result must have one reason")
        if self.status.startswith("SUCCESS_") and (
            len(self.profiles) + self.invalid_result_count
            != self.provider_result_count
        ):
            raise ValueError("valid and invalid results must reconcile to provider results")
        if self.status == "SUCCESS_WITH_RESULTS":
            if not self.profiles:
                raise ValueError("SUCCESS_WITH_RESULTS requires profiles")
            if self.error_code is not None or self.error_message is not None:
                raise ValueError("successful retrieval cannot contain an error")
        elif self.status == "SUCCESS_ZERO_RESULTS":
            if self.profiles or self.provider_result_count:
                raise ValueError("SUCCESS_ZERO_RESULTS cannot contain provider results")
            if self.error_code is not None or self.error_message is not None:
                raise ValueError("successful retrieval cannot contain an error")
        else:
            _required_text(self.error_code, "error_code")
            _required_text(self.error_message, "error_message")
            if self.profiles:
                raise ValueError("failed or skipped retrieval cannot contain profiles")
        if self.status == "SKIPPED_NOT_CONFIGURED" and self.error_code != "configuration_missing":
            raise ValueError("skipped queries must use configuration_missing")
        if any(profile.platform != self.platform for profile in self.profiles):
            raise ValueError("every profile must match the query platform")
        if any(profile.query_id != self.query_id for profile in self.profiles):
            raise ValueError("every profile must reference the query_id")
        if any(profile.run_id != self.run_id for profile in self.profiles):
            raise ValueError("every profile must reference the run_id")

    @property
    def retrieved_count(self) -> int:
        return len(self.profiles)

    @property
    def duration_seconds(self) -> float:
        from datetime import datetime

        started = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
        completed = datetime.fromisoformat(self.completed_at.replace("Z", "+00:00"))
        return max(0.0, (completed - started).total_seconds())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiscoveryRunResult:
    """Unified controlled/live result with independent per-query outcomes."""

    run_id: str
    campaign_id: str
    approved_search_plan_id: str
    discovery_mode: str
    query_results: tuple[DiscoveryQueryResult, ...]
    started_at: str
    completed_at: str

    def __post_init__(self) -> None:
        for field_name in (
            "run_id",
            "campaign_id",
            "approved_search_plan_id",
            "started_at",
            "completed_at",
        ):
            _required_text(getattr(self, field_name), field_name)
        if self.discovery_mode not in DISCOVERY_RUN_MODES:
            raise ValueError(
                f"discovery_mode must be one of {sorted(DISCOVERY_RUN_MODES)}"
            )
        query_ids = [result.query_id for result in self.query_results]
        if len(query_ids) != len(set(query_ids)):
            raise ValueError("each approved query can have only one result")
        if any(result.run_id != self.run_id for result in self.query_results):
            raise ValueError("every query result must reference the run_id")
        if any(result.campaign_id != self.campaign_id for result in self.query_results):
            raise ValueError("every query result must reference the campaign_id")
        if any(
            result.approved_search_plan_id != self.approved_search_plan_id
            for result in self.query_results
        ):
            raise ValueError("every query result must reference the Approved Search Plan")

    @property
    def profiles(self) -> tuple[RawCreatorProfile, ...]:
        return tuple(
            profile for result in self.query_results for profile in result.profiles
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QueryExecutionHistory:
    """Persistable post-dedup evidence for one approved query execution."""

    run_id: str
    campaign_id: str
    approved_search_plan_id: str
    query_id: str
    platform: str
    source_connector: str
    query_text: str
    search_angle: str
    execution_status: str
    retrieved: int
    duplicates: int
    new_creators: int
    new_creator_yield: float | None
    error_code: str | None
    started_at: str
    completed_at: str

    def __post_init__(self) -> None:
        for field_name in (
            "run_id",
            "campaign_id",
            "approved_search_plan_id",
            "query_id",
            "platform",
            "source_connector",
            "query_text",
            "search_angle",
            "started_at",
            "completed_at",
        ):
            _required_text(getattr(self, field_name), field_name)
        if self.platform not in PLATFORMS:
            raise ValueError(f"platform must be one of {sorted(PLATFORMS)}")
        if self.execution_status not in QUERY_EXECUTION_STATUSES:
            raise ValueError(
                f"execution_status must be one of {sorted(QUERY_EXECUTION_STATUSES)}"
            )
        if min(self.retrieved, self.duplicates, self.new_creators) < 0:
            raise ValueError("query history counts cannot be negative")
        if self.duplicates + self.new_creators != self.retrieved:
            raise ValueError("duplicates and new creators must reconcile to retrieved")
        if self.execution_status.startswith("SUCCESS_"):
            expected = self.new_creators / self.retrieved if self.retrieved else 0.0
            if self.new_creator_yield is None or abs(self.new_creator_yield - expected) > 1e-12:
                raise ValueError("successful query yield must match query counts")
            if self.error_code is not None:
                raise ValueError("successful query history cannot contain an error")
        else:
            if self.new_creator_yield is not None:
                raise ValueError("failed or skipped query yield must be null")
            _required_text(self.error_code, "error_code")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
