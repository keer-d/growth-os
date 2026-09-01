"""Deterministic V1 deduplication with explainable duplicate results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from domain.models import RawCreatorProfile


@dataclass(frozen=True)
class DuplicateRecord:
    record: RawCreatorProfile
    reason: str
    matched_key: tuple[str, str]
    matched_record_id: str


@dataclass(frozen=True)
class DedupResult:
    new_records: tuple[RawCreatorProfile, ...]
    duplicate_records: tuple[DuplicateRecord, ...]


def deduplicate_creators(
    creators: Sequence[RawCreatorProfile],
    existing_keys: Mapping[tuple[str, str], str] | None = None,
) -> DedupResult:
    """Deduplicate only by same platform plus normalized profile URL."""
    seen = dict(existing_keys or {})
    new_records: list[RawCreatorProfile] = []
    duplicate_records: list[DuplicateRecord] = []

    for creator in creators:
        key = creator.dedup_key
        matched_record_id = seen.get(key)
        if matched_record_id:
            duplicate_records.append(
                DuplicateRecord(
                    record=creator,
                    reason="same platform + same normalized profile URL",
                    matched_key=key,
                    matched_record_id=matched_record_id,
                )
            )
            continue
        seen[key] = creator.record_id
        new_records.append(creator)

    return DedupResult(tuple(new_records), tuple(duplicate_records))
