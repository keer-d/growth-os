"""Small, explicit contracts shared by the backend pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


PLATFORMS = {"instagram", "x"}
DISCOVERY_MODES = {"controlled_demo", "live", "live_instagram"}
PRIORITIES = {"P1", "P2", "P3", "Needs Review"}
REVIEW_STATUSES = {"approve", "reject", "needs_review"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class ContentSample:
    text: str
    url: str | None
    published_at: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContentSample":
        return cls(
            text=_required_text(data.get("text"), "content_samples[].text"),
            url=data.get("url"),
            published_at=data.get("published_at"),
        )


@dataclass(frozen=True)
class RawCreatorProfile:
    """Observed creator facts plus retrieval provenance and one derived URL.

    ``profile_url`` is never overwritten. ``normalized_profile_url`` is a
    separately derived system value used only for deterministic identity.
    """

    record_id: str
    platform: str
    profile_url: str
    normalized_profile_url: str
    display_name: str | None
    bio_text: str | None
    follower_count: int | None
    external_urls: tuple[str, ...]
    content_samples: tuple[ContentSample, ...]
    discovery_mode: str
    source_connector: str
    run_id: str
    query_id: str
    retrieved_at: str
    campaign_id: str | None = None
    approved_search_plan_id: str | None = None
    source_query_id: str | None = None
    query_text: str | None = None
    search_angle: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "record_id",
            "profile_url",
            "normalized_profile_url",
            "source_connector",
            "run_id",
            "query_id",
            "retrieved_at",
        ):
            _required_text(getattr(self, name), name)
        if self.platform not in PLATFORMS:
            raise ValueError(f"platform must be one of {sorted(PLATFORMS)}")
        if self.discovery_mode not in DISCOVERY_MODES:
            raise ValueError(f"discovery_mode must be one of {sorted(DISCOVERY_MODES)}")
        if self.follower_count is not None and self.follower_count < 0:
            raise ValueError("follower_count cannot be negative")
        if self.discovery_mode == "live_instagram":
            for name in (
                "campaign_id",
                "approved_search_plan_id",
                "source_query_id",
                "query_text",
                "search_angle",
            ):
                _required_text(getattr(self, name), name)

    @property
    def dedup_key(self) -> tuple[str, str]:
        return self.platform, self.normalized_profile_url

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Signal:
    value: str
    reason: str
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CreatorSignals:
    record_id: str
    activity: Signal
    content_relevance: Signal
    audience_size: Signal
    market: Signal
    actionability: Signal
    record_quality: Signal
    extracted_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AudienceInference:
    record_id: str
    likely_audience: tuple[str, ...]
    evidence: tuple[str, ...]
    confidence: str
    provider: str
    model: str
    prompt_version: str
    inferred_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PriorityDecision:
    record_id: str
    priority: str
    reasons: tuple[str, ...]
    signal_evidence: dict[str, dict[str, Any]]
    decided_at: str

    def __post_init__(self) -> None:
        if self.priority not in PRIORITIES:
            raise ValueError(f"priority must be one of {sorted(PRIORITIES)}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QueryHistory:
    query_id: str
    run_id: str
    source_connector: str
    query_text: str
    retrieved: int
    duplicates: int
    new_creators: int
    new_creator_yield: float

    @classmethod
    def from_counts(
        cls,
        *,
        query_id: str,
        run_id: str,
        source_connector: str,
        query_text: str,
        retrieved: int,
        duplicates: int,
        new_creators: int,
    ) -> "QueryHistory":
        value = new_creators / retrieved if retrieved else 0.0
        return cls(
            query_id=query_id,
            run_id=run_id,
            source_connector=source_connector,
            query_text=query_text,
            retrieved=retrieved,
            duplicates=duplicates,
            new_creators=new_creators,
            new_creator_yield=value,
        )


@dataclass(frozen=True)
class Review:
    record_id: str
    status: str
    structured_reason: str | None
    comment: str | None
    reviewed_at: str

    def __post_init__(self) -> None:
        if self.status not in REVIEW_STATUSES:
            raise ValueError(f"status must be one of {sorted(REVIEW_STATUSES)}")


@dataclass(frozen=True)
class Feedback:
    record_id: str
    feedback_type: str
    comment: str | None
    created_at: str
    review_id: int | None = None
