"""Contracts for provider-proposed, non-executable creator search plans."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from domain.models import PLATFORMS


SEARCH_ANGLES = {
    "core_topic",
    "creator_workflow",
    "audience_problem",
    "adjacent_tool",
    "professional_identity",
    "use_case",
}
SEARCH_PLAN_STATUSES = {"draft"}


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class SearchQuery:
    """One human-reviewable query proposal; it does not authorize retrieval."""

    query_id: str
    campaign_id: str
    platform: str
    query_text: str
    rationale: str
    search_angle: str

    def __post_init__(self) -> None:
        for field_name in ("query_id", "campaign_id", "query_text", "rationale"):
            _required_text(getattr(self, field_name), field_name)
        if self.platform not in PLATFORMS:
            raise ValueError(f"platform must be one of {sorted(PLATFORMS)}")
        if self.search_angle not in SEARCH_ANGLES:
            raise ValueError(f"search_angle must be one of {sorted(SEARCH_ANGLES)}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SearchPlanProvenance:
    provider: str
    model: str
    prompt_version: str
    generated_at: str

    def __post_init__(self) -> None:
        for field_name in ("provider", "model", "prompt_version", "generated_at"):
            _required_text(getattr(self, field_name), field_name)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DraftSearchPlan:
    """A validated proposal that remains separate from review and execution."""

    search_plan_id: str
    campaign_id: str
    status: str
    queries: tuple[SearchQuery, ...]
    provenance: SearchPlanProvenance

    def __post_init__(self) -> None:
        _required_text(self.search_plan_id, "search_plan_id")
        _required_text(self.campaign_id, "campaign_id")
        if self.status not in SEARCH_PLAN_STATUSES:
            raise ValueError(f"status must be one of {sorted(SEARCH_PLAN_STATUSES)}")
        if not self.queries:
            raise ValueError("queries must not be empty")

        query_ids = [query.query_id for query in self.queries]
        if len(query_ids) != len(set(query_ids)):
            raise ValueError("query_id values must be unique within a search plan")
        if any(query.campaign_id != self.campaign_id for query in self.queries):
            raise ValueError("every query must reference the plan campaign_id")

        normalized_texts = [" ".join(query.query_text.casefold().split()) for query in self.queries]
        if len(normalized_texts) != len(set(normalized_texts)):
            raise ValueError("exact duplicate query_text values are not allowed")

        platforms = {query.platform for query in self.queries}
        if platforms != PLATFORMS:
            raise ValueError(f"a draft plan must cover each platform: {sorted(PLATFORMS)}")
        if len({query.search_angle for query in self.queries}) < 3:
            raise ValueError("a draft plan must contain at least three distinct search angles")
        for platform in PLATFORMS:
            platform_angles = {
                query.search_angle for query in self.queries if query.platform == platform
            }
            if len(platform_angles) < 2:
                raise ValueError(f"{platform} queries must use at least two search angles")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
