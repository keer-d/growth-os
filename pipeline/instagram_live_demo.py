"""One-query safe smoke test for approved Instagram live retrieval."""

from __future__ import annotations

from collections import Counter
import os
from uuid import uuid4

from pipeline.audience import DeterministicAudienceProvider
from pipeline.campaign_demo import load_campaign_briefs
from pipeline.dedup import deduplicate_creators
from pipeline.instagram_retrieval import (
    ApifyInstagramConfiguration,
    ApifyInstagramSearchProvider,
    InstagramLiveRetrievalAdapter,
    InstagramProviderConfigurationError,
)
from pipeline.prioritize import prioritize_creator
from pipeline.search_plan_demo import run_reviewed_search_plan_demo
from pipeline.signals import extract_signals


def run_safe_live_test() -> dict:
    """Run at most one approved query, or return not-executed without a token."""

    if not os.getenv("APIFY_API_TOKEN", "").strip():
        return {
            "status": "not_executed",
            "reason": "APIFY_API_TOKEN is not configured",
            "live_query_count": 0,
            "downstream_executed": False,
        }

    try:
        configuration = ApifyInstagramConfiguration.from_environment()
        results_per_query = _results_limit_from_environment()
    except InstagramProviderConfigurationError as exc:
        return {
            "status": "not_executed",
            "reason": exc.safe_message,
            "error_code": exc.error_code,
            "live_query_count": 0,
            "downstream_executed": False,
        }

    brief = {
        item.campaign_id: item for item in load_campaign_briefs()
    }["campaign_demo_001"]
    _, _, _, approved_plan = run_reviewed_search_plan_demo(brief=brief)
    provider = ApifyInstagramSearchProvider(configuration)
    retrieval = InstagramLiveRetrievalAdapter(
        provider, results_per_query=results_per_query
    ).retrieve(
        approved_plan,
        run_id=f"live_instagram_{uuid4().hex[:12]}",
        query_limit=1,
    )
    query_result = retrieval.query_results[0]
    if query_result.status == "failed":
        return {
            "status": "executed_failed",
            "run_id": retrieval.run_id,
            "query_id": query_result.query_id,
            "query_text": query_result.query_text,
            "error_code": query_result.error_code,
            "error_message": query_result.error_message,
            "live_query_count": 1,
            "downstream_executed": False,
        }

    deduped = deduplicate_creators(retrieval.profiles)
    audience_provider = DeterministicAudienceProvider()
    decisions = []
    for profile in deduped.new_records:
        signals = extract_signals(profile)
        inference = audience_provider.infer(profile, signals)
        decisions.append(prioritize_creator(signals, inference))
    priority_counts = Counter(decision.priority for decision in decisions)
    return {
        "status": "executed_succeeded",
        "run_id": retrieval.run_id,
        "query_id": query_result.query_id,
        "query_text": query_result.query_text,
        "live_query_count": 1,
        "provider_results": query_result.provider_result_count,
        "valid_raw_profiles": len(retrieval.profiles),
        "invalid_provider_results": query_result.invalid_result_count,
        "duplicates": len(deduped.duplicate_records),
        "new_creators": len(deduped.new_records),
        "priority_counts": {
            label: priority_counts.get(label, 0)
            for label in ("P1", "P2", "P3", "Needs Review")
        },
        "downstream_executed": True,
    }


def print_live_test(summary: dict) -> None:
    print("INSTAGRAM LIVE RETRIEVAL — SAFE ONE-QUERY TEST")
    print(f"Status: {summary['status']}")
    if summary["status"] == "not_executed":
        print(f"Reason: {summary['reason']}")
        print("No provider request was made.")
        return
    print(f"Run ID: {summary['run_id']}")
    print(f"Approved query: {summary['query_text']}")
    if summary["status"] == "executed_failed":
        print(f"Error: {summary['error_code']}: {summary['error_message']}")
        print("Downstream: not executed")
        return
    print(f"Provider results: {summary['provider_results']}")
    print(f"Valid RawCreatorProfile records: {summary['valid_raw_profiles']}")
    print(f"Invalid provider results: {summary['invalid_provider_results']}")
    print(f"Duplicates: {summary['duplicates']}")
    print(f"New creators: {summary['new_creators']}")
    print("Priority counts:")
    for label, count in summary["priority_counts"].items():
        print(f"  {label}: {count}")


def _results_limit_from_environment() -> int:
    raw = os.getenv("APIFY_INSTAGRAM_RESULTS_LIMIT", "").strip()
    if not raw:
        return 3
    try:
        value = int(raw)
    except ValueError as exc:
        raise InstagramProviderConfigurationError(
            "invalid_provider_configuration",
            "APIFY_INSTAGRAM_RESULTS_LIMIT must be an integer",
        ) from exc
    if not 1 <= value <= 10:
        raise InstagramProviderConfigurationError(
            "invalid_provider_configuration",
            "APIFY_INSTAGRAM_RESULTS_LIMIT must be between 1 and 10",
        )
    return value


def main() -> None:
    print_live_test(run_safe_live_test())


if __name__ == "__main__":
    main()
