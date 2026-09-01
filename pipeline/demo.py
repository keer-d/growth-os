"""Run the backend-only Controlled Demo end to end."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from domain.models import Feedback, Review, utc_now_iso
from pipeline.audience import DeterministicAudienceProvider
from pipeline.dedup import deduplicate_creators
from pipeline.history import build_query_history
from pipeline.prioritize import prioritize_creator
from pipeline.read_creators import load_creators
from pipeline.signals import extract_signals
from storage.sqlite_store import SQLiteStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = PROJECT_ROOT / "fixtures" / "controlled_demo_minimal.json"
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "controlled_demo.db"
QUERY_TEXTS = {
    "query_01": "portfolio and personal website creators in US or Canada",
    "query_02": "active freelance and no-code design educators",
    "query_03": "website creators with partnership signals",
    "query_04": "broader AI and creative-tool discovery",
}


def run_controlled_demo(
    *,
    fixture_path: str | Path = DEFAULT_FIXTURE,
    database_path: str | Path = DEFAULT_DATABASE,
    reset: bool = False,
    seed_synthetic_review: bool = True,
) -> dict[str, Any]:
    database_path = Path(database_path)
    if reset and database_path.exists():
        database_path.unlink()

    started_at = utc_now_iso()
    creators = load_creators(fixture_path)
    if not creators:
        raise ValueError("controlled demo fixture is empty")
    run_id = creators[0].run_id
    if any(item.run_id != run_id for item in creators):
        raise ValueError("controlled demo fixture must use one run_id")

    provider = DeterministicAudienceProvider()
    decisions = []
    with SQLiteStore(database_path) as store:
        dedup_result = deduplicate_creators(creators, store.existing_creator_keys())
        completed_at = utc_now_iso()
        store.save_run(
            run_id=run_id,
            discovery_mode="controlled_demo",
            started_at=started_at,
            completed_at=completed_at,
            retrieved=len(creators),
            duplicates=len(dedup_result.duplicate_records),
            new_creators=len(dedup_result.new_records),
        )
        histories = build_query_history(creators, dedup_result, QUERY_TEXTS)
        for history in histories:
            store.save_query_history(history)

        for profile in dedup_result.new_records:
            store.save_creator(profile)
            signals = extract_signals(profile)
            store.save_signals(signals)
            inference = provider.infer(profile, signals)
            store.save_audience_inference(inference)
            decision = prioritize_creator(signals, inference)
            store.save_priority_decision(decision)
            decisions.append(decision)

        if seed_synthetic_review and decisions:
            review_target = next(
                (item for item in decisions if item.record_id == "creator_009"),
                next((item for item in decisions if item.priority == "Needs Review"), decisions[0]),
            )
            review = Review(
                record_id=review_target.record_id,
                status="needs_review",
                structured_reason="insufficient_or_conflicting_evidence",
                comment="Synthetic Controlled Demo review; no automatic learning is triggered.",
                reviewed_at=utc_now_iso(),
            )
            review_id = store.add_review(review)
            store.add_feedback(
                Feedback(
                    record_id=review_target.record_id,
                    review_id=review_id,
                    feedback_type="evidence_gap",
                    comment="Synthetic feedback stored for later analysis only.",
                    created_at=utc_now_iso(),
                )
            )

        priority_counts = Counter(item.priority for item in decisions)
        summary = {
            "run_id": run_id,
            "database_path": str(database_path),
            "retrieved": len(creators),
            "duplicates": len(dedup_result.duplicate_records),
            "new_creators": len(dedup_result.new_records),
            "new_creator_yield": (
                len(dedup_result.new_records) / len(creators) if creators else 0.0
            ),
            "priority_counts": {
                label: priority_counts.get(label, 0)
                for label in ("P1", "P2", "P3", "Needs Review")
            },
            "queries": [history.__dict__ for history in histories],
            "reviews_stored": store.count("reviews"),
            "feedback_stored": store.count("feedback"),
        }
    return summary


def print_summary(summary: dict[str, Any]) -> None:
    print(f"RUN ID: {summary['run_id']}")
    print(f"Retrieved: {summary['retrieved']}")
    print(f"Duplicates: {summary['duplicates']}")
    print(f"New creators: {summary['new_creators']}")
    print(f"New Creator Yield: {summary['new_creator_yield']:.1%}")
    print("\nPriority:")
    for label, count in summary["priority_counts"].items():
        print(f"  {label}: {count}")
    print(f"\nReviews stored: {summary['reviews_stored']}")
    print(f"Feedback stored: {summary['feedback_stored']}")
    print(f"SQLite: {summary['database_path']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Creator Discovery OS Controlled Demo.")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--db-path", default=str(DEFAULT_DATABASE))
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Remove only the selected local demo database before running.",
    )
    parser.add_argument(
        "--no-synthetic-review",
        action="store_true",
        help="Skip the one clearly labeled synthetic review/feedback example.",
    )
    args = parser.parse_args()
    summary = run_controlled_demo(
        fixture_path=args.fixture,
        database_path=args.db_path,
        reset=args.reset,
        seed_synthetic_review=not args.no_synthetic_review,
    )
    print_summary(summary)


if __name__ == "__main__":
    main()
