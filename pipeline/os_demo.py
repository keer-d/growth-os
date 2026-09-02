"""Command-line demonstration of the complete Creator Discovery OS V1 backend."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from pipeline.campaign_demo import load_campaign_briefs
from pipeline.os_runner import execute_approved_plan, prepare_demo_campaign
from storage.sqlite_store import SQLiteStoreError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "creator_discovery_os_v1.db"


def run_os_demo(
    *,
    mode: str,
    database_path: str | Path = DEFAULT_DATABASE,
    reset: bool = False,
    runs: int = 1,
) -> dict:
    if mode not in {"controlled", "live"}:
        raise ValueError("mode must be controlled or live")
    if runs < 1:
        raise ValueError("runs must be positive")
    if mode == "live" and runs != 1:
        raise ValueError("live mode permits exactly one run per command")
    database_path = Path(database_path)
    if reset and database_path.exists():
        database_path.unlink()

    brief = {
        item.campaign_id: item for item in load_campaign_briefs()
    }["campaign_demo_001"]
    prepared = prepare_demo_campaign(brief)
    summaries = [
        execute_approved_plan(
            prepared["approved_plan"],
            mode=mode,
            database_path=database_path,
            seed_controlled_review=index == 0,
        )
        for index in range(runs)
    ]
    return {**prepared, "runs": summaries, "database_path": str(database_path)}


def print_os_demo(result: dict) -> None:
    campaign = result["campaign_result"]
    draft = result["draft_plan"]
    review = result["review"]
    approved = result["approved_plan"]
    print("CREATOR DISCOVERY OS V1 BACKEND")
    print("\nCAMPAIGN")
    print(f"  {campaign.brief.original_brief}")
    print(f"  Structured status: {campaign.status}")
    print("\n↓ DRAFT SEARCH PLAN")
    print(f"  {len(draft.queries)} AI-proposed queries; status={draft.status}")
    print("\n↓ HUMAN REVIEW")
    counts = {decision: 0 for decision in ("approved", "edited", "rejected")}
    for item in review.reviewed_queries:
        counts[item.decision] += 1
    print(
        f"  {counts['approved']} approved, {counts['edited']} edited, "
        f"{counts['rejected']} rejected"
    )
    print("\n↓ APPROVED QUERIES")
    print(f"  {len(approved.queries)} executable queries")
    print("  " + ", ".join(f"{q.platform}:{q.search_angle}" for q in approved.queries))

    for index, summary in enumerate(result["runs"], start=1):
        print(f"\n↓ DISCOVERY RUN {index}")
        print(f"  Run ID: {summary['run_id']}")
        print(f"  Mode: {summary['mode']}; status: {summary['run_status']}")
        for query in summary["query_history"]:
            yield_text = (
                "n/a"
                if query["new_creator_yield"] is None
                else f"{query['new_creator_yield']:.1%}"
            )
            error = f"; error={query['error_code']}" if query["error_code"] else ""
            print(
                f"  {query['platform']} | {query['search_angle']} | "
                f"{query['execution_status']} | retrieved={query['retrieved']} | "
                f"duplicates={query['duplicates']} | new={query['new_creators']} | "
                f"yield={yield_text}{error}"
            )
        print("\n↓ RETRIEVED / DEDUP / NEW")
        print(
            f"  {summary['retrieved']} retrieved → {summary['duplicates']} duplicates "
            f"→ {summary['new_creators']} new ({summary['new_creator_yield']:.1%} yield)"
        )
        print("\n↓ SIGNALS / AI AUDIENCE / PRIORITY")
        print(
            f"  signals={summary['signals']}; "
            f"audience_inferences={summary['audience_inferences']}; "
            f"priority={summary['priority_counts']}"
        )

    final = result["runs"][-1]
    print("\n↓ DATABASE")
    print(f"  SQLite: {result['database_path']}")
    print(f"  Stored counts: {final['stored_counts']}")
    print("\n↓ RUN HISTORY / SATURATION EVIDENCE")
    for row in final["run_history"]:
        print(
            f"  {row['run_id']} | {row['status']} | retrieved={row['retrieved']} | "
            f"duplicates={row['duplicates']} | new={row['new_creators']} | "
            f"yield={row['new_creator_yield']:.1%}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Creator Discovery OS V1 backend.")
    parser.add_argument("--mode", choices=("controlled", "live"), default="controlled")
    parser.add_argument("--db-path", default=str(DEFAULT_DATABASE))
    parser.add_argument("--reset", action="store_true")
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Controlled-only repeat runs for real saturation evidence.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        result = run_os_demo(
            mode=args.mode,
            database_path=args.db_path,
            reset=args.reset,
            runs=args.runs,
        )
    except SQLiteStoreError as exc:
        parser.error(f"{exc.error_code}: {exc.safe_message}")
    print_os_demo(result)


if __name__ == "__main__":
    main()
