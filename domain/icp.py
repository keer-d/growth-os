"""Contracts for testable customer ICP hypotheses and discovery translation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from domain.campaign import CampaignDefinition


ICP_DIMENSIONS = (
    "pain_severity",
    "problem_frequency",
    "value_proposition_strength",
    "reachability",
    "intent_signal_availability",
    "potential_commercial_value",
    "product_fit",
)
ICP_STATUSES = {"DRAFT", "TESTING", "PAUSED", "VALIDATED", "INVALIDATED"}
CRITERIA_STATUSES = {"incomplete", "draft", "confirmed"}
SUPPORTED_DISCOVERY_CHANNELS = {"instagram", "x", "youtube", "web"}


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be text or null")
    return value.strip() or None


def _text_tuple(value: Any, field_name: str, *, required: bool = False) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be an array")
    cleaned = tuple(_required_text(item, f"{field_name} item") for item in value)
    if required and not cleaned:
        raise ValueError(f"{field_name} must not be empty")
    return cleaned


@dataclass(frozen=True)
class BusinessContext:
    """Human-confirmed facts used to generate ICP hypotheses."""

    context_id: str
    product_name: str
    website_url: str | None
    product_description: str | None
    problem: str
    strongest_value: str
    current_users: str
    current_alternatives: tuple[str, ...]
    pain_signals: tuple[str, ...]
    target_markets: tuple[str, ...]
    stage: str
    created_at: str

    def __post_init__(self) -> None:
        for field_name in (
            "context_id",
            "product_name",
            "problem",
            "strongest_value",
            "current_users",
            "stage",
            "created_at",
        ):
            _required_text(getattr(self, field_name), field_name)
        object.__setattr__(self, "website_url", _optional_text(self.website_url, "website_url"))
        object.__setattr__(
            self,
            "product_description",
            _optional_text(self.product_description, "product_description"),
        )
        if not self.website_url and not self.product_description:
            raise ValueError("product_description or website_url is required")
        for field_name in ("current_alternatives", "pain_signals", "target_markets"):
            object.__setattr__(self, field_name, _text_tuple(getattr(self, field_name), field_name))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ICPEvaluation:
    """AI-estimated comparison dimensions, never presented as market truth."""

    pain_severity: int
    problem_frequency: int
    value_proposition_strength: int
    reachability: int
    intent_signal_availability: int
    potential_commercial_value: int
    product_fit: int

    def __post_init__(self) -> None:
        for field_name in ICP_DIMENSIONS:
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
                raise ValueError(f"{field_name} must be an integer from 0 to 100")

    @property
    def comparison_score(self) -> int:
        return round(sum(getattr(self, name) for name in ICP_DIMENSIONS) / len(ICP_DIMENSIONS))

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["comparison_score"] = self.comparison_score
        return result


@dataclass(frozen=True)
class ICPHypothesis:
    """One immutable, versioned customer hypothesis proposed for testing."""

    hypothesis_id: str
    version: int
    business_context_id: str
    audience_type: str
    name: str
    who: str
    context: str
    core_pain: str
    why_pain_matters: str
    current_alternative: str
    value_proposition: str
    trigger: str
    intent_signals: tuple[str, ...]
    where_to_find: tuple[str, ...]
    why_may_work: str
    unknowns: tuple[str, ...]
    evaluation: ICPEvaluation
    recommended_order: int
    test_priority_reason: str
    status: str
    created_at: str

    def __post_init__(self) -> None:
        for field_name in (
            "hypothesis_id",
            "business_context_id",
            "name",
            "who",
            "context",
            "core_pain",
            "why_pain_matters",
            "current_alternative",
            "value_proposition",
            "trigger",
            "why_may_work",
            "test_priority_reason",
            "created_at",
        ):
            _required_text(getattr(self, field_name), field_name)
        if self.audience_type not in {"customer", "partner"}:
            raise ValueError("audience_type must be customer or partner")
        if not isinstance(self.version, int) or self.version < 1:
            raise ValueError("version must be a positive integer")
        if self.status not in ICP_STATUSES:
            raise ValueError(f"status must be one of {sorted(ICP_STATUSES)}")
        if self.recommended_order not in {1, 2, 3}:
            raise ValueError("recommended_order must be 1, 2, or 3")
        object.__setattr__(self, "intent_signals", _text_tuple(self.intent_signals, "intent_signals", required=True))
        object.__setattr__(self, "where_to_find", _text_tuple(self.where_to_find, "where_to_find", required=True))
        object.__setattr__(self, "unknowns", _text_tuple(self.unknowns, "unknowns", required=True))

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["evaluation"]["comparison_score"] = self.evaluation.comparison_score
        return result


@dataclass(frozen=True)
class ICPGenerationProvenance:
    provider: str
    model: str
    prompt_version: str
    generated_at: str
    duration_ms: int

    def __post_init__(self) -> None:
        for field_name in ("provider", "model", "prompt_version", "generated_at"):
            _required_text(getattr(self, field_name), field_name)
        if not isinstance(self.duration_ms, int) or self.duration_ms < 0:
            raise ValueError("duration_ms must be a non-negative integer")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ICPGenerationResult:
    context: BusinessContext
    hypotheses: tuple[ICPHypothesis, ...]
    provenance: ICPGenerationProvenance
    status: str
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"complete", "failed"}:
            raise ValueError("status must be complete or failed")
        if self.status == "complete" and len(self.hypotheses) != 3:
            raise ValueError("a complete ICP generation must contain exactly three hypotheses")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ICPSelection:
    selection_id: str
    hypothesis_id: str
    hypothesis_version: int
    status: str
    selected_at: str

    def __post_init__(self) -> None:
        for field_name in ("selection_id", "hypothesis_id", "selected_at"):
            _required_text(getattr(self, field_name), field_name)
        if self.hypothesis_version < 1:
            raise ValueError("hypothesis_version must be positive")
        if self.status != "TESTING":
            raise ValueError("a new ICP selection must have TESTING status")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiscoveryCriteria:
    """Human-reviewable bridge from a customer ICP to partner discovery."""

    criteria_id: str
    source_criteria_id: str | None
    hypothesis_id: str
    hypothesis_version: int
    hypothesis_name: str
    discovery_subject: str
    partner_profile: str
    goal: str
    target_markets: tuple[str, ...]
    content_themes: tuple[str, ...]
    target_audience: tuple[str, ...]
    intent_signals: tuple[str, ...]
    exclusions: tuple[str, ...]
    channels: tuple[str, ...]
    status: str
    criteria_version: str
    created_at: str
    confirmed_at: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "criteria_id",
            "hypothesis_id",
            "hypothesis_name",
            "partner_profile",
            "goal",
            "criteria_version",
            "created_at",
        ):
            _required_text(getattr(self, field_name), field_name)
        if self.source_criteria_id is not None:
            _required_text(self.source_criteria_id, "source_criteria_id")
        if self.hypothesis_version < 1:
            raise ValueError("hypothesis_version must be positive")
        if self.discovery_subject != "partner":
            raise ValueError("V1 discovery_subject must be partner")
        if self.status not in CRITERIA_STATUSES:
            raise ValueError(f"status must be one of {sorted(CRITERIA_STATUSES)}")
        for field_name in (
            "target_markets",
            "content_themes",
            "target_audience",
            "intent_signals",
            "exclusions",
            "channels",
        ):
            object.__setattr__(self, field_name, _text_tuple(getattr(self, field_name), field_name))
        unknown_channels = set(self.channels) - SUPPORTED_DISCOVERY_CHANNELS
        if unknown_channels:
            raise ValueError(f"unsupported discovery channels: {sorted(unknown_channels)}")
        if self.status == "confirmed":
            missing = [
                name
                for name in ("target_markets", "content_themes", "target_audience", "channels")
                if not getattr(self, name)
            ]
            if missing:
                raise ValueError("confirmed criteria missing: " + ", ".join(missing))
            if len(self.channels) < 2:
                raise ValueError("confirmed criteria must cover at least two channels")
            _required_text(self.confirmed_at, "confirmed_at")

    def to_campaign_definition(self, campaign_id: str) -> CampaignDefinition:
        if self.status != "confirmed":
            raise ValueError("only confirmed discovery criteria can become a campaign")
        return CampaignDefinition(
            campaign_id=_required_text(campaign_id, "campaign_id"),
            goal=self.goal,
            target_markets=self.target_markets,
            content_themes=self.content_themes,
            target_audience=self.target_audience,
            exclusions=self.exclusions,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ICPRunContext:
    hypothesis_id: str
    hypothesis_version: int
    hypothesis_name: str
    hypothesis_created_at: str
    selected_at: str
    criteria_id: str
    criteria_snapshot: dict[str, Any]

    def __post_init__(self) -> None:
        for field_name in (
            "hypothesis_id",
            "hypothesis_name",
            "hypothesis_created_at",
            "selected_at",
            "criteria_id",
        ):
            _required_text(getattr(self, field_name), field_name)
        if self.hypothesis_version < 1:
            raise ValueError("hypothesis_version must be positive")
        if not isinstance(self.criteria_snapshot, dict):
            raise ValueError("criteria_snapshot must be an object")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
