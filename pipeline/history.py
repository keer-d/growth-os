"""Minimal run/query performance calculation."""

from __future__ import annotations

from collections import Counter
from typing import Mapping, Sequence

from domain.models import QueryHistory, RawCreatorProfile
from pipeline.dedup import DedupResult


def build_query_history(
    creators: Sequence[RawCreatorProfile],
    dedup_result: DedupResult,
    query_texts: Mapping[str, str],
) -> list[QueryHistory]:
    retrieved = Counter(item.query_id for item in creators)
    duplicates = Counter(item.record.query_id for item in dedup_result.duplicate_records)
    new_creators = Counter(item.query_id for item in dedup_result.new_records)
    source_by_query = {item.query_id: item.source_connector for item in creators}
    run_by_query = {item.query_id: item.run_id for item in creators}

    return [
        QueryHistory.from_counts(
            query_id=query_id,
            run_id=run_by_query[query_id],
            source_connector=source_by_query[query_id],
            query_text=query_texts.get(query_id, "controlled demo query"),
            retrieved=count,
            duplicates=duplicates[query_id],
            new_creators=new_creators[query_id],
        )
        for query_id, count in sorted(retrieved.items())
    ]
