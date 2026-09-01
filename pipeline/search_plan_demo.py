"""Human-readable offline demo from Campaign Brief to Draft Search Plan."""

from __future__ import annotations

import argparse
import json

from domain.campaign import CampaignBrief, CampaignParseResult
from domain.search_plan import DraftSearchPlan
from pipeline.campaign_demo import load_campaign_briefs
from pipeline.campaign_parser import CampaignBriefParser, DeterministicCampaignProvider
from pipeline.search_plan import (
    DeterministicSearchPlanProvider,
    EnvironmentLLMSearchPlanProvider,
    SearchPlanGenerator,
    SearchPlanProviderConfigurationError,
)


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


def print_search_plan_demo(campaign_result, plan: DraftSearchPlan | None) -> None:
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
        campaign_result, plan = run_search_plan_demo(
            brief=fixtures[args.fixture_id], provider_mode=args.provider
        )
    except SearchPlanProviderConfigurationError as exc:
        parser.error(str(exc))
    print_search_plan_demo(campaign_result, plan)


if __name__ == "__main__":
    main()
