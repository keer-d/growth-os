"""Contracts for human campaign briefs and provider-derived definitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


PARSE_STATUSES = {"complete", "incomplete", "needs_clarification", "failed"}


def _non_empty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class CampaignBrief:
    """Observed human input. The original text is preserved byte-for-byte."""

    campaign_id: str
    original_brief: str

    def __post_init__(self) -> None:
        _non_empty(self.campaign_id, "campaign_id")
        _non_empty(self.original_brief, "original_brief")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CampaignDefinition:
    """Provider-neutral structured interpretation of one CampaignBrief."""

    campaign_id: str
    goal: str | None
    target_markets: tuple[str, ...]
    content_themes: tuple[str, ...]
    target_audience: tuple[str, ...]
    exclusions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CampaignParseProvenance:
    provider: str
    model: str
    prompt_version: str
    parsed_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CampaignParseResult:
    brief: CampaignBrief
    definition: CampaignDefinition | None
    status: str
    missing_required_fields: tuple[str, ...]
    clarification_questions: tuple[str, ...]
    provenance: CampaignParseProvenance
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.status not in PARSE_STATUSES:
            raise ValueError(f"status must be one of {sorted(PARSE_STATUSES)}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
