"""Structured outcomes for approved-query creator retrieval."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from domain.models import RawCreatorProfile


RETRIEVAL_STATUSES = {"succeeded", "failed"}


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
