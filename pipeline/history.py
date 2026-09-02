"""Minimal run/query performance calculation."""

from __future__ import annotations

from collections import Counter
from typing import Mapping, Sequence

from domain.models import QueryHistory, RawCreatorProfile
from domain.retrieval import DiscoveryRunResult, QueryExecutionHistory
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


def build_execution_history(
    run: DiscoveryRunResult,
    dedup_result: DedupResult,
) -> list[QueryExecutionHistory]:
    """Calculate real post-dedup metrics without converting failures into zero results."""

    duplicates = Counter(item.record.query_id for item in dedup_result.duplicate_records)
    new_creators = Counter(item.query_id for item in dedup_result.new_records)
    histories = []
    for result in run.query_results:
        retrieved = result.retrieved_count
        duplicate_count = duplicates[result.query_id]
        new_count = new_creators[result.query_id]
        successful = result.status.startswith("SUCCESS_")
        histories.append(
            QueryExecutionHistory(
                run_id=run.run_id,
                campaign_id=run.campaign_id,
                approved_search_plan_id=run.approved_search_plan_id,
                query_id=result.query_id,
                platform=result.platform,
                source_connector=result.source_connector,
                query_text=result.query_text,
                search_angle=result.search_angle,
                execution_status=result.status,
                retrieved=retrieved,
                duplicates=duplicate_count,
                new_creators=new_count,
                new_creator_yield=(new_count / retrieved if retrieved else 0.0)
                if successful
                else None,
                error_code=result.error_code,
                started_at=result.started_at,
                completed_at=result.completed_at,
            )
        )
    return histories
