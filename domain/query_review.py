"""Immutable contracts for human query review and approved search plans."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from domain.models import PLATFORMS
from domain.search_plan import SEARCH_ANGLES, SearchQuery


REVIEW_DECISIONS = {"approved", "rejected", "edited"}
EXECUTABLE_DECISIONS = {"approved", "edited"}
REVIEW_STATUSES = {"complete"}
APPROVED_PLAN_STATUSES = {"approved"}


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, field_name: str) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise ValueError(f"{field_name} must be null or a non-empty string")


def _normalized_query_text(value: str) -> str:
    return " ".join(value.casefold().split())


@dataclass(frozen=True)
class QueryReviewAction:
    """One human decision submitted for a Draft Search Plan query."""

    query_id: str
    decision: str
    edited_query_text: str | None = None
    human_comment: str | None = None
    reviewed_at: str | None = None

    def __post_init__(self) -> None:
        _required_text(self.query_id, "query_id")
        if self.decision not in REVIEW_DECISIONS:
            raise ValueError(f"decision must be one of {sorted(REVIEW_DECISIONS)}")
        _optional_text(self.human_comment, "human_comment")
        _optional_text(self.reviewed_at, "reviewed_at")
        if self.decision == "edited":
            _required_text(self.edited_query_text, "edited_query_text")
        elif self.edited_query_text is not None:
            raise ValueError("edited_query_text is allowed only when decision is edited")


@dataclass(frozen=True)
class ReviewedQuery:
    """Traceability record preserving the complete original AI proposal."""

    original_query: SearchQuery
    final_query_text: str | None
    decision: str
    human_comment: str | None
    reviewed_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.original_query, SearchQuery):
            raise ValueError("original_query must be a SearchQuery")
        if self.decision not in REVIEW_DECISIONS:
            raise ValueError(f"decision must be one of {sorted(REVIEW_DECISIONS)}")
        _optional_text(self.human_comment, "human_comment")
        _required_text(self.reviewed_at, "reviewed_at")

        if self.decision == "approved":
            if self.final_query_text != self.original_query.query_text:
                raise ValueError("approved query final text must equal the original query text")
        elif self.decision == "rejected":
            if self.final_query_text is not None:
                raise ValueError("rejected query final text must be null")
        else:
            final_text = _required_text(self.final_query_text, "final_query_text")
            if _normalized_query_text(final_text) == _normalized_query_text(
                self.original_query.query_text
            ):
                raise ValueError("edited query final text must differ from the original")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SearchPlanReview:
    """Complete human audit trail, including rejected Draft queries."""

    review_id: str
    draft_search_plan_id: str
    campaign_id: str
    status: str
    reviewed_queries: tuple[ReviewedQuery, ...]
    completed_at: str

    def __post_init__(self) -> None:
        for field_name in (
            "review_id",
            "draft_search_plan_id",
            "campaign_id",
            "completed_at",
        ):
            _required_text(getattr(self, field_name), field_name)
        if self.status not in REVIEW_STATUSES:
            raise ValueError(f"status must be one of {sorted(REVIEW_STATUSES)}")
        if not self.reviewed_queries:
            raise ValueError("reviewed_queries must not be empty")
        query_ids = [item.original_query.query_id for item in self.reviewed_queries]
        if len(query_ids) != len(set(query_ids)):
            raise ValueError("each Draft query can be reviewed only once")
        if any(
            item.original_query.campaign_id != self.campaign_id
            for item in self.reviewed_queries
        ):
            raise ValueError("every reviewed query must reference the review campaign_id")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedSearchQuery:
    """One human-approved query that may be passed to a future retrieval layer."""

    query_id: str
    source_query_id: str
    campaign_id: str
    platform: str
    query_text: str
    search_angle: str
    review_decision: str

    def __post_init__(self) -> None:
        for field_name in ("query_id", "source_query_id", "campaign_id", "query_text"):
            _required_text(getattr(self, field_name), field_name)
        if self.platform not in PLATFORMS:
            raise ValueError(f"platform must be one of {sorted(PLATFORMS)}")
        if self.search_angle not in SEARCH_ANGLES:
            raise ValueError(f"search_angle must be one of {sorted(SEARCH_ANGLES)}")
        if self.review_decision not in EXECUTABLE_DECISIONS:
            raise ValueError(
                f"review_decision must be one of {sorted(EXECUTABLE_DECISIONS)}"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedSearchPlan:
    """Executable query contract produced only by a complete human review."""

    approved_search_plan_id: str
    source_draft_search_plan_id: str
    review_id: str
    campaign_id: str
    status: str
    queries: tuple[ApprovedSearchQuery, ...]
    approved_at: str

    def __post_init__(self) -> None:
        for field_name in (
            "approved_search_plan_id",
            "source_draft_search_plan_id",
            "review_id",
            "campaign_id",
            "approved_at",
        ):
            _required_text(getattr(self, field_name), field_name)
        if self.status not in APPROVED_PLAN_STATUSES:
            raise ValueError(f"status must be one of {sorted(APPROVED_PLAN_STATUSES)}")
        if not self.queries:
            raise ValueError("an Approved Search Plan must contain at least one query")

        query_ids = [query.query_id for query in self.queries]
        source_ids = [query.source_query_id for query in self.queries]
        if len(query_ids) != len(set(query_ids)):
            raise ValueError("approved query_id values must be unique")
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("a Draft query can enter an Approved Search Plan only once")
        if any(query.campaign_id != self.campaign_id for query in self.queries):
            raise ValueError("every approved query must reference the plan campaign_id")

        normalized_texts = [
            _normalized_query_text(query.query_text) for query in self.queries
        ]
        if len(normalized_texts) != len(set(normalized_texts)):
            raise ValueError("duplicate final query text is not allowed")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
