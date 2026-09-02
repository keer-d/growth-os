"""End-to-end V1 processing from approved discovery through SQLite history."""

from __future__ import annotations

from collections import Counter
import json
import logging
from pathlib import Path
from typing import Any

from domain.campaign import CampaignBrief
from domain.icp import ICPRunContext
from domain.models import Feedback, Review, utc_now_iso
from domain.query_review import ApprovedSearchPlan
from domain.retrieval import DiscoveryRunResult
from pipeline.audience import DeterministicAudienceProvider
from pipeline.dedup import deduplicate_creators
from pipeline.discovery import UnifiedDiscoveryRunner
from pipeline.history import build_execution_history
from pipeline.prioritize import prioritize_creator
from pipeline.search_plan_demo import run_reviewed_search_plan_demo
from pipeline.signals import extract_signals
from storage.sqlite_store import SQLiteStore


LOGGER = logging.getLogger("creator_discovery.run")


def prepare_demo_campaign(brief: CampaignBrief) -> dict[str, Any]:
    """Run the deterministic Campaign, Draft, and Human Review layers."""

    campaign, draft, review, approved = run_reviewed_search_plan_demo(brief=brief)
    if campaign.status != "complete" or campaign.definition is None:
        raise ValueError("the end-to-end demo requires a complete Campaign Definition")
    if draft is None or review is None or approved is None:
        raise ValueError("the end-to-end demo requires a complete approved search plan")
    return {
        "campaign_result": campaign,
        "draft_plan": draft,
        "review": review,
        "approved_plan": approved,
    }


def execute_approved_plan(
    approved_plan: ApprovedSearchPlan,
    *,
    mode: str,
    database_path: str | Path,
    discovery_runner: UnifiedDiscoveryRunner | None = None,
    seed_controlled_review: bool = True,
    icp_run_context: ICPRunContext | None = None,
) -> dict[str, Any]:
    """Retrieve, deduplicate, process, and atomically persist one discovery run."""

    runner = discovery_runner or UnifiedDiscoveryRunner()
    retrieval = runner.run(approved_plan, mode=mode)
    audience_provider = DeterministicAudienceProvider()
    decisions = []

    with SQLiteStore(database_path) as store:
        deduped = deduplicate_creators(retrieval.profiles, store.existing_creator_keys())
        histories = build_execution_history(retrieval, deduped)
        run_status, run_error = _run_status(retrieval)
        store.save_run(
            run_id=retrieval.run_id,
            discovery_mode=mode,
            campaign_id=retrieval.campaign_id,
            approved_search_plan_id=retrieval.approved_search_plan_id,
            status=run_status,
            error_code=run_error,
            started_at=retrieval.started_at,
            completed_at=retrieval.completed_at,
            retrieved=len(retrieval.profiles),
            duplicates=len(deduped.duplicate_records),
            new_creators=len(deduped.new_records),
        )
        for history in histories:
            store.save_query_execution(history)

        if icp_run_context is not None:
            store.save_icp_run_link(
                run_id=retrieval.run_id,
                context=icp_run_context,
                linked_at=utc_now_iso(),
            )

        for profile in deduped.new_records:
            store.save_creator(profile)
            signals = extract_signals(profile)
            store.save_signals(signals)
            inference = audience_provider.infer(profile, signals)
            store.save_audience_inference(inference)
            decision = prioritize_creator(signals, inference)
            store.save_priority_decision(decision)
            decisions.append(decision)

        if mode == "controlled" and seed_controlled_review and decisions:
            _store_synthetic_review(store, decisions[0].record_id)

        priority_counts = Counter(item.priority for item in decisions)
        stored_counts = {
            table: store.count(table)
            for table in (
                "runs",
                "query_executions",
                "creators",
                "creator_signals",
                "audience_inferences",
                "priority_decisions",
                "reviews",
                "feedback",
            )
        }
        saturation = [dict(row) for row in store.get_saturation_evidence()]
        run_history = [dict(row) for row in store.get_run_history()]

    summary = {
        "run_id": retrieval.run_id,
        "mode": mode,
        "database_path": str(Path(database_path)),
        "run_status": run_status,
        "run_error_code": run_error,
        "retrieved": len(retrieval.profiles),
        "duplicates": len(deduped.duplicate_records),
        "new_creators": len(deduped.new_records),
        "new_creator_yield": (
            len(deduped.new_records) / len(retrieval.profiles)
            if retrieval.profiles
            else 0.0
        ),
        "signals": len(decisions),
        "audience_inferences": len(decisions),
        "priority_counts": {
            label: priority_counts.get(label, 0)
            for label in ("P1", "P2", "P3", "Needs Review")
        },
        "query_history": [history.to_dict() for history in histories],
        "stored_counts": stored_counts,
        "saturation_evidence": saturation,
        "run_history": run_history,
        "retrieval": retrieval,
    }
    LOGGER.info(
        json.dumps(
            {
                "event": "run_persisted",
                "run_id": retrieval.run_id,
                "status": run_status,
                "retrieved": summary["retrieved"],
                "duplicates": summary["duplicates"],
                "new_creators": summary["new_creators"],
            },
            sort_keys=True,
        )
    )
    return summary


def _run_status(retrieval: DiscoveryRunResult) -> tuple[str, str | None]:
    statuses = {result.status for result in retrieval.query_results}
    if statuses == {"SKIPPED_NOT_CONFIGURED"}:
        return "SKIPPED_NOT_CONFIGURED", "configuration_missing"
    if "FAILED" in statuses or "SKIPPED_NOT_CONFIGURED" in statuses:
        return "COMPLETED_WITH_ISSUES", "partial_query_failure"
    return "COMPLETED", None


def _store_synthetic_review(store: SQLiteStore, record_id: str) -> None:
    review_id = store.add_review(
        Review(
            record_id=record_id,
            status="needs_review",
            structured_reason="controlled_demo_human_review_example",
            comment="Synthetic review stored for the Controlled Demo only.",
            reviewed_at=utc_now_iso(),
        )
    )
    store.add_feedback(
        Feedback(
            record_id=record_id,
            review_id=review_id,
            feedback_type="useful",
            comment="Synthetic feedback is stored but does not alter queries or rules.",
            created_at=utc_now_iso(),
        )
    )
