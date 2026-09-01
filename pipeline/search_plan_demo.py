"""Human-readable offline demo from Campaign Brief to Draft Search Plan."""

from __future__ import annotations

import argparse
from collections import Counter
import json

from domain.campaign import CampaignBrief, CampaignParseResult
from domain.query_review import (
    ApprovedSearchPlan,
    QueryReviewAction,
    SearchPlanReview,
)
from domain.search_plan import DraftSearchPlan
from pipeline.campaign_demo import load_campaign_briefs
from pipeline.campaign_parser import CampaignBriefParser, DeterministicCampaignProvider
from pipeline.search_plan import (
    DeterministicSearchPlanProvider,
    EnvironmentLLMSearchPlanProvider,
    SearchPlanGenerator,
    SearchPlanProviderConfigurationError,
)
from pipeline.query_review import HumanQueryReviewer


def run_search_plan_demo(
    *, brief: CampaignBrief, provider_mode: str = "mock"
) -> tuple[CampaignParseResult, DraftSearchPlan | None]:
    campaign_result = CampaignBriefParser(DeterministicCampaignProvider()).parse(brief)
    if campaign_result.status != "complete" or campaign_result.definition is None:
        return campaign_result, None

    if provider_mode == "mock":
        provider = DeterministicSearchPlanProvider()
    elif provider_mode == "live":
        provider = EnvironmentLLMSearchPlanProvider()
    else:
        raise ValueError("provider_mode must be 'mock' or 'live'")
    plan = SearchPlanGenerator(provider).generate(campaign_result.definition)
    return campaign_result, plan


def synthetic_review_actions(plan: DraftSearchPlan) -> tuple[QueryReviewAction, ...]:
    """Return the fixed 5 approve / 2 edit / 1 reject Controlled Demo review."""

    if len(plan.queries) != 8:
        raise ValueError("the synthetic review expects the default 8-query Draft plan")
    decisions = (
        "approved",
        "approved",
        "edited",
        "approved",
        "approved",
        "rejected",
        "edited",
        "approved",
    )
    actions = []
    for index, (query, decision) in enumerate(zip(plan.queries, decisions), start=1):
        edited_query_text = None
        human_comment = None
        if index == 3:
            edited_query_text = query.query_text.replace(" sharing ", " teaching ")
            human_comment = "Use a clearer educational-content angle."
        elif index == 6:
            human_comment = "Too problem-focused for this first search pass."
        elif index == 7:
            edited_query_text = query.query_text.replace(" tools for ", " software for ")
            human_comment = "Use the more common software wording."
        actions.append(
            QueryReviewAction(
                query_id=query.query_id,
                decision=decision,
                edited_query_text=edited_query_text,
                human_comment=human_comment,
                reviewed_at=f"2026-08-15T10:00:{index:02d}Z",
            )
        )
    return tuple(actions)


def run_reviewed_search_plan_demo(
    *, brief: CampaignBrief, provider_mode: str = "mock"
) -> tuple[
    CampaignParseResult,
    DraftSearchPlan | None,
    SearchPlanReview | None,
    ApprovedSearchPlan | None,
]:
    campaign_result, draft_plan = run_search_plan_demo(
        brief=brief, provider_mode=provider_mode
    )
    if draft_plan is None:
        return campaign_result, None, None, None
    review, approved_plan = HumanQueryReviewer().review(
        draft_plan,
        synthetic_review_actions(draft_plan),
        completed_at="2026-08-15T10:00:09Z",
    )
    return campaign_result, draft_plan, review, approved_plan


def print_search_plan_demo(
    campaign_result,
    plan: DraftSearchPlan | None,
    review: SearchPlanReview | None = None,
    approved_plan: ApprovedSearchPlan | None = None,
) -> None:
    print("ORIGINAL BRIEF")
    print(campaign_result.brief.original_brief)
    print("\n→ STRUCTURED CAMPAIGN DEFINITION")
    if campaign_result.definition is None:
        print("null")
    else:
        print(json.dumps(campaign_result.definition.to_dict(), indent=2, ensure_ascii=False))

    print("\n→ DRAFT SEARCH PLAN")
    if plan is None:
        print("NOT GENERATED")
        print(f"Campaign parse status: {campaign_result.status}")
        if campaign_result.missing_required_fields:
            print("Missing required fields: " + ", ".join(campaign_result.missing_required_fields))
        return

    print(f"Search plan ID: {plan.search_plan_id}")
    print(f"Campaign ID: {plan.campaign_id}")
    print(f"Status: {plan.status}")
    for platform in ("instagram", "x"):
        platform_queries = [query for query in plan.queries if query.platform == platform]
        print(f"\n{platform.upper()} ({len(platform_queries)} queries)")
        for query in platform_queries:
            print(f"- {query.query_text}")
            print(f"  ID: {query.query_id}")
            print(f"  Angle: {query.search_angle}")
            print(f"  Why: {query.rationale}")
    print("\nGENERATION PROVENANCE")
    print(json.dumps(plan.provenance.to_dict(), indent=2, ensure_ascii=False))

    if review is None or approved_plan is None:
        return

    counts = Counter(item.decision for item in review.reviewed_queries)
    print("\n→ HUMAN QUERY REVIEW")
    print(f"Review ID: {review.review_id}")
    print(f"Status: {review.status}")
    print(
        "Decisions: "
        f"{counts['approved']} approved, "
        f"{counts['edited']} edited, "
        f"{counts['rejected']} rejected"
    )
    for item in review.reviewed_queries:
        print(f"- {item.decision.upper()}: {item.original_query.query_text}")
        print(f"  Final: {item.final_query_text or '[not executable]'}")
        if item.human_comment:
            print(f"  Comment: {item.human_comment}")

    print("\n→ APPROVED SEARCH PLAN")
    print(f"Approved plan ID: {approved_plan.approved_search_plan_id}")
    print(f"Source Draft plan ID: {approved_plan.source_draft_search_plan_id}")
    print(f"Status: {approved_plan.status}")
    print(f"Executable queries: {len(approved_plan.queries)}")
    for platform in ("instagram", "x"):
        platform_queries = [
            query for query in approved_plan.queries if query.platform == platform
        ]
        print(f"\n{platform.upper()} ({len(platform_queries)} executable)")
        for query in platform_queries:
            print(f"- {query.query_text} [{query.review_decision}]")
            print(f"  ID: {query.query_id}")
            print(f"  Source Draft query: {query.source_query_id}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Turn a structured Campaign Definition into a Draft Search Plan."
    )
    parser.add_argument("--fixture-id", default="campaign_demo_001")
    parser.add_argument("--provider", choices=("mock", "live"), default="mock")
    args = parser.parse_args()

    fixtures = {item.campaign_id: item for item in load_campaign_briefs()}
    if args.fixture_id not in fixtures:
        parser.error(f"unknown fixture ID: {args.fixture_id}")
    try:
        campaign_result, plan, review, approved_plan = run_reviewed_search_plan_demo(
            brief=fixtures[args.fixture_id], provider_mode=args.provider
        )
    except SearchPlanProviderConfigurationError as exc:
        parser.error(str(exc))
    print_search_plan_demo(campaign_result, plan, review, approved_plan)


if __name__ == "__main__":
    main()
