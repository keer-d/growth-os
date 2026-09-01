"""Load observed fixture records into the formal raw creator contract."""

from __future__ import annotations

import json
from pathlib import Path

from domain.models import ContentSample, RawCreatorProfile
from pipeline.normalize import normalize_profile_url


def load_creators(path: str | Path) -> list[RawCreatorProfile]:
    with Path(path).open(encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise ValueError("creator fixture must contain a JSON array")

    creators = []
    for row in rows:
        platform = row.get("platform")
        profile_url = row.get("profile_url")
        creators.append(
            RawCreatorProfile(
                record_id=row.get("record_id"),
                platform=platform,
                profile_url=profile_url,
                normalized_profile_url=normalize_profile_url(profile_url, platform),
                display_name=row.get("display_name"),
                bio_text=row.get("bio_text"),
                follower_count=row.get("follower_count"),
                external_urls=tuple(row.get("external_urls") or []),
                content_samples=tuple(
                    ContentSample.from_dict(item) for item in (row.get("content_samples") or [])
                ),
                discovery_mode=row.get("discovery_mode"),
                source_connector=row.get("source_connector"),
                run_id=row.get("run_id"),
                query_id=row.get("query_id"),
                retrieved_at=row.get("retrieved_at"),
            )
        )
    return creators
