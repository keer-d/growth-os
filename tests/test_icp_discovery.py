import json
from pathlib import Path
import tempfile
import unittest

from domain.icp import BusinessContext
from domain.models import utc_now_iso
from pipeline.icp_discovery import (
    DeterministicICPProvider,
    ICPDiscoveryService,
    ICPProvider,
    IncompleteDiscoveryCriteriaError,
    MalformedICPOutputError,
    WebsiteContextUnavailableError,
    confirm_discovery_criteria,
    generate_discovery_criteria,
    next_hypothesis_version,
)
from pipeline.ui_service import CreatorDiscoveryUIService
from storage.sqlite_store import SQLiteStore


PAYLOAD = {
    "product_name": "ClipForge AI",
    "website_url": None,
    "product_description": (
        "AI video generation workspace that turns product information into "
        "launch, demo, and social campaign videos."
    ),
    "problem": (
        "Producing polished campaign video is slow, expensive, and dependent "
        "on scarce production specialists."
    ),
    "strongest_value": (
        "Create usable product and campaign videos in hours instead of a "
        "multi-day production workflow."
    ),
    "current_users": "product marketers, growth teams, and small agencies",
    "current_alternatives": ["freelance editors", "internal video teams"],
    "pain_signals": ["hiring video editors", "announcing product launches"],
    "target_markets": ["United States", "Canada"],
    "stage": "early",
}


def context(*, markets=("United States", "Canada"), description=PAYLOAD["product_description"]):
    return BusinessContext(
        context_id="context_test",
        product_name=PAYLOAD["product_name"],
        website_url="https://example.com" if description is None else None,
        product_description=description,
        problem=PAYLOAD["problem"],
        strongest_value=PAYLOAD["strongest_value"],
        current_users=PAYLOAD["current_users"],
        current_alternatives=tuple(PAYLOAD["current_alternatives"]),
        pain_signals=tuple(PAYLOAD["pain_signals"]),
        target_markets=markets,
        stage="early",
        created_at=utc_now_iso(),
    )


class StaticProvider(ICPProvider):
    provider_name = "test"
    model_name = "test-model"

    def __init__(self, output):
        self.output = output

    def generate(self, context):
        return self.output


class ICPDiscoveryTests(unittest.TestCase):
    def test_offline_generation_returns_exactly_three_testable_hypotheses(self):
        result = ICPDiscoveryService(DeterministicICPProvider()).generate(context())
        self.assertEqual(result.status, "complete")
        self.assertEqual(len(result.hypotheses), 3)
        self.assertEqual(len({item.name for item in result.hypotheses}), 3)
        self.assertEqual([item.recommended_order for item in result.hypotheses], [1, 2, 3])
        self.assertTrue(all(item.unknowns for item in result.hypotheses))
        self.assertTrue(all(item.status == "DRAFT" for item in result.hypotheses))

    def test_website_only_is_explicitly_unsupported_in_offline_mode(self):
        with self.assertRaises(WebsiteContextUnavailableError):
            ICPDiscoveryService(DeterministicICPProvider()).generate(
                context(description=None)
            )

    def test_malformed_provider_output_is_rejected(self):
        provider = StaticProvider(json.dumps({"hypotheses": [{"name": "Only one"}]}))
        with self.assertRaises(MalformedICPOutputError):
            ICPDiscoveryService(provider).generate(context())

    def test_edit_creates_v2_without_mutating_v1(self):
        original = ICPDiscoveryService(DeterministicICPProvider()).generate(
            context()
        ).hypotheses[0]
        edited = next_hypothesis_version(original, {"who": "Edited customer definition"})
        self.assertEqual(original.version, 1)
        self.assertNotEqual(original.who, edited.who)
        self.assertEqual(edited.version, 2)

        with tempfile.TemporaryDirectory() as directory:
            with SQLiteStore(Path(directory) / "icp.db") as store:
                store.save_business_context(context())
                store.save_icp_hypothesis(original)
                store.save_icp_hypothesis(edited)
                self.assertEqual(store.count("icp_hypotheses"), 2)
                self.assertEqual(
                    store.get_icp_hypothesis(original.hypothesis_id, 1).who,
                    original.who,
                )

    def test_missing_market_blocks_criteria_confirmation_without_invention(self):
        empty_market_context = context(markets=())
        hypothesis = ICPDiscoveryService(DeterministicICPProvider()).generate(
            empty_market_context
        ).hypotheses[0]
        draft = generate_discovery_criteria(hypothesis, empty_market_context)
        self.assertEqual(draft.status, "incomplete")
        with self.assertRaises(IncompleteDiscoveryCriteriaError):
            confirm_discovery_criteria(
                draft,
                partner_profile=draft.partner_profile,
                goal=draft.goal,
                target_markets=(),
                content_themes=draft.content_themes,
                target_audience=draft.target_audience,
                intent_signals=draft.intent_signals,
                exclusions=(),
                channels=draft.channels,
            )


class ICPWorkflowIntegrationTests(unittest.TestCase):
    def test_icp_to_existing_discovery_preserves_versions_links_and_events(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "growth.db"
            service = CreatorDiscoveryUIService(database)
            generated = service.generate_icp_hypotheses(PAYLOAD)
            original = generated["hypotheses"][0]
            edited = service.edit_icp_hypothesis(
                hypothesis_id=original["hypothesis_id"],
                version=1,
                changes={"who": original["who"] + " The team owns a quarterly pipeline target."},
            )
            selected = service.select_icp_hypothesis(
                hypothesis_id=edited["hypothesis_id"], version=2
            )
            criteria = selected["criteria"]
            workflow = service.confirm_icp_criteria(
                criteria_id=criteria["criteria_id"], payload=criteria
            )
            self.assertEqual(workflow["confirmed_criteria"]["status"], "confirmed")
            self.assertEqual(workflow["draft_search_plan"]["status"], "draft")
            self.assertEqual(workflow["icp_context"]["hypothesis_version"], 2)
            actions = [
                {"query_id": item["query_id"], "decision": "approved"}
                for item in workflow["draft_search_plan"]["queries"]
            ]
            result = service.run_discovery(
                workflow_id=workflow["workflow_id"],
                actions=actions,
                mode="controlled",
            )

            with SQLiteStore(database) as store:
                self.assertEqual(store.count("icp_hypotheses"), 4)
                self.assertEqual(store.count("icp_run_links"), 1)
                link = dict(store.get_icp_runs()[0])
                self.assertEqual(link["run_id"], result["run_summary"]["run_id"])
                self.assertEqual(link["hypothesis_version"], 2)
                event_names = {row["event_name"] for row in store.get_product_events()}
            self.assertTrue(
                {
                    "icp_discovery_started",
                    "business_context_completed",
                    "icp_hypotheses_generated",
                    "icp_hypothesis_selected",
                    "icp_hypothesis_edited",
                    "discovery_criteria_generated",
                    "discovery_criteria_confirmed",
                    "discovery_run_started_from_icp",
                }.issubset(event_names)
            )


if __name__ == "__main__":
    unittest.main()
