"""Human-readable backend demo for Campaign Brief parsing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import uuid4

from domain.campaign import CampaignBrief
from pipeline.campaign_parser import (
    CampaignBriefParser,
    CampaignProviderConfigurationError,
    DeterministicCampaignProvider,
    EnvironmentLLMCampaignProvider,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES = PROJECT_ROOT / "fixtures" / "campaign_briefs.json"


def load_campaign_briefs(path: str | Path = DEFAULT_FIXTURES) -> list[CampaignBrief]:
    with Path(path).open(encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise ValueError("campaign fixture must contain a JSON array")
    return [CampaignBrief(row["campaign_id"], row["original_brief"]) for row in rows]


def run_campaign_demo(
    *,
    brief: CampaignBrief,
    provider_mode: str = "mock",
):
    if provider_mode == "mock":
        provider = DeterministicCampaignProvider()
    elif provider_mode == "live":
        provider = EnvironmentLLMCampaignProvider()
    else:
        raise ValueError("provider_mode must be 'mock' or 'live'")
    return CampaignBriefParser(provider).parse(brief)


def print_campaign_result(result) -> None:
    print(f"CAMPAIGN ID: {result.brief.campaign_id}")
    print("\nORIGINAL BRIEF:")
    print(result.brief.original_brief)
    print(f"\nPARSE STATUS: {result.status}")
    print("\nSTRUCTURED CAMPAIGN DEFINITION:")
    if result.definition is None:
        print("null")
    else:
        print(json.dumps(result.definition.to_dict(), indent=2, ensure_ascii=False))
    if result.missing_required_fields:
        print("\nMISSING REQUIRED FIELDS:")
        for field in result.missing_required_fields:
            print(f"  - {field}")
    if result.clarification_questions:
        print("\nCLARIFICATION QUESTIONS:")
        for question in result.clarification_questions:
            print(f"  - {question}")
    if result.error_code:
        print(f"\nERROR: {result.error_code}: {result.error_message}")
    print("\nPARSE PROVENANCE:")
    print(json.dumps(result.provenance.to_dict(), indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a natural-language Campaign Brief.")
    parser.add_argument("--brief", help="Parse this brief instead of a synthetic fixture.")
    parser.add_argument("--campaign-id", help="ID to use with --brief.")
    parser.add_argument("--fixture-id", default="campaign_demo_001")
    parser.add_argument("--provider", choices=("mock", "live"), default="mock")
    args = parser.parse_args()

    if args.brief:
        brief = CampaignBrief(
            campaign_id=args.campaign_id or f"campaign_{uuid4().hex[:12]}",
            original_brief=args.brief,
        )
    else:
        fixtures = {item.campaign_id: item for item in load_campaign_briefs()}
        if args.fixture_id not in fixtures:
            parser.error(f"unknown fixture ID: {args.fixture_id}")
        brief = fixtures[args.fixture_id]

    try:
        result = run_campaign_demo(brief=brief, provider_mode=args.provider)
    except CampaignProviderConfigurationError as exc:
        parser.error(str(exc))
    print_campaign_result(result)


if __name__ == "__main__":
    main()
