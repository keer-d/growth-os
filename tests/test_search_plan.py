import json
import os
import unittest
from unittest.mock import patch

from domain.campaign import CampaignDefinition
from domain.models import CHANNEL_ORDER, PLATFORMS
from domain.search_plan import SEARCH_ANGLES
from pipeline.campaign_demo import load_campaign_briefs
from pipeline.campaign_parser import CampaignBriefParser, DeterministicCampaignProvider
from pipeline.search_plan import (
    DeterministicSearchPlanProvider,
    EnvironmentLLMSearchPlanProvider,
    IncompleteCampaignError,
    MalformedSearchPlanOutput,
    MAX_QUERIES,
    SearchPlanGenerator,
    SearchPlanProvider,
    SearchPlanProviderConfigurationError,
    fitting_channels,
)
from pipeline.search_plan_demo import run_search_plan_demo


class StaticSearchPlanProvider(SearchPlanProvider):
    provider_name = "static-test"
    model_name = "static-test-model"

    def __init__(self, payload):
        self.payload = payload
        self.called = False

    def generate(self, campaign: CampaignDefinition) -> str:
        self.called = True
        return json.dumps(self.payload)


class SearchPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.briefs = {brief.campaign_id: brief for brief in load_campaign_briefs()}

    def campaign_result(self, campaign_id):
        return CampaignBriefParser(DeterministicCampaignProvider()).parse(
            self.briefs[campaign_id]
        )

    def generate_fixture(self, campaign_id):
        result = self.campaign_result(campaign_id)
        self.assertEqual(result.status, "complete")
        return SearchPlanGenerator(DeterministicSearchPlanProvider()).generate(result.definition)

    def test_us_canada_campaign_generates_linked_multi_channel_draft(self):
        plan = self.generate_fixture("campaign_demo_001")
        self.assertEqual(plan.status, "draft")
        self.assertEqual(plan.campaign_id, "campaign_demo_001")
        self.assertEqual(len(plan.queries), 14)
        self.assertLessEqual(len(plan.queries), MAX_QUERIES)
        self.assertEqual(
            {platform: sum(query.platform == platform for query in plan.queries)
             for platform in CHANNEL_ORDER},
            {"instagram": 4, "x": 4, "youtube": 3, "web": 3},
        )
        self.assertTrue(all(query.platform in PLATFORMS for query in plan.queries))
        self.assertTrue(all(query.campaign_id == plan.campaign_id for query in plan.queries))
        self.assertEqual(len({query.query_id for query in plan.queries}), len(plan.queries))

    def test_youtube_and_web_queries_read_as_their_own_channel(self):
        plan = self.generate_fixture("campaign_demo_001")
        youtube = [query.query_text.casefold() for query in plan.queries if query.platform == "youtube"]
        web = [query.query_text.casefold() for query in plan.queries if query.platform == "web"]
        self.assertTrue(
            all(
                any(word in text for word in ("tutorial", "walkthrough", "review"))
                for text in youtube
            ),
            youtube,
        )
        self.assertTrue(
            all(
                any(word in text for word in ("blog", "resources", "writing about"))
                for text in web
            ),
            web,
        )
        # A YouTube query must not be a copy of the Instagram or X query text.
        other = {
            query.query_text.casefold()
            for query in plan.queries
            if query.platform in ("instagram", "x")
        }
        self.assertFalse(other & set(youtube + web))

    def test_channel_fit_is_read_from_the_campaign_not_hardcoded(self):
        portfolio = self.campaign_result("campaign_demo_001").definition
        self.assertEqual(fitting_channels(portfolio), ("instagram", "x", "youtube", "web"))
        # Nothing in this definition implies demonstrable craft or an industry
        # press, so the proposer must stay on the two always-on channels.
        narrow = CampaignDefinition(
            campaign_id="campaign_fit_001",
            goal="Discover partners for potential collaborations",
            target_markets=("United States",),
            content_themes=("home cooking",),
            target_audience=("home cooks",),
            exclusions=(),
        )
        self.assertEqual(fitting_channels(narrow), ("instagram", "x"))
        plan = SearchPlanGenerator(DeterministicSearchPlanProvider()).generate(narrow)
        self.assertEqual({query.platform for query in plan.queries}, {"instagram", "x"})

    def test_plans_use_multiple_meaningful_angles_and_nonempty_explanations(self):
        plan = self.generate_fixture("campaign_demo_001")
        self.assertGreaterEqual(len({query.search_angle for query in plan.queries}), 5)
        for platform in ("instagram", "x"):
            angles = {
                query.search_angle for query in plan.queries if query.platform == platform
            }
            self.assertGreaterEqual(len(angles), 4)
        for platform in ("youtube", "web"):
            angles = {
                query.search_angle for query in plan.queries if query.platform == platform
            }
            self.assertGreaterEqual(len(angles), 3)
        self.assertTrue(all(query.search_angle in SEARCH_ANGLES for query in plan.queries))
        self.assertTrue(all(query.query_text.strip() for query in plan.queries))
        self.assertTrue(all(query.rationale.strip() for query in plan.queries))

    def test_uk_ireland_no_code_web_design_fixture_is_supported(self):
        plan = self.generate_fixture("campaign_demo_002")
        text = " | ".join(query.query_text for query in plan.queries).casefold()
        self.assertIn("no-code", text)
        self.assertIn("web design", text)
        self.assertIn("uk ireland", text)

    def test_explicit_exclusions_do_not_become_search_targets(self):
        plan = self.generate_fixture("campaign_demo_004")
        text = " | ".join(query.query_text for query in plan.queries).casefold()
        self.assertNotIn("agencies", text)
        self.assertNotIn("corporate brand accounts", text)

    def test_incomplete_campaign_is_blocked_before_provider_call(self):
        result = self.campaign_result("campaign_demo_003")
        self.assertEqual(result.status, "incomplete")
        provider = StaticSearchPlanProvider({"queries": []})
        with self.assertRaises(IncompleteCampaignError):
            SearchPlanGenerator(provider).generate(result.definition)
        self.assertFalse(provider.called)

        campaign_result, plan = run_search_plan_demo(brief=self.briefs["campaign_demo_003"])
        self.assertEqual(campaign_result.status, "incomplete")
        self.assertIsNone(plan)

    def test_mock_generation_is_deterministic_and_offline(self):
        campaign = self.campaign_result("campaign_demo_001").definition
        with patch.dict(os.environ, {}, clear=True):
            first = SearchPlanGenerator(DeterministicSearchPlanProvider()).generate(campaign)
            second = SearchPlanGenerator(DeterministicSearchPlanProvider()).generate(campaign)
        self.assertEqual(first.search_plan_id, second.search_plan_id)
        self.assertEqual(first.queries, second.queries)
        self.assertEqual(first.provenance.provider, "mock")

    def test_exact_duplicate_query_text_is_removed(self):
        payload = {"queries": [
            {"platform": "instagram", "query_text": "AI website creator", "rationale": "Core.", "search_angle": "core_topic"},
            {"platform": "instagram", "query_text": "  ai WEBSITE creator ", "rationale": "Duplicate.", "search_angle": "use_case"},
            {"platform": "instagram", "query_text": "portfolio workflow", "rationale": "Workflow.", "search_angle": "creator_workflow"},
            {"platform": "x", "query_text": "building websites with AI", "rationale": "Core.", "search_angle": "core_topic"},
            {"platform": "x", "query_text": "portfolio problems for freelancers", "rationale": "Problems.", "search_angle": "audience_problem"},
        ]}
        campaign = self.campaign_result("campaign_demo_001").definition
        plan = SearchPlanGenerator(StaticSearchPlanProvider(payload)).generate(campaign)
        self.assertEqual(len(plan.queries), 4)
        self.assertEqual(
            len({" ".join(query.query_text.casefold().split()) for query in plan.queries}),
            4,
        )

    def test_malformed_provider_output_fails_explicitly(self):
        campaign = self.campaign_result("campaign_demo_001").definition
        invalid = StaticSearchPlanProvider({"queries": [
            {"platform": "linkedin", "query_text": "web design", "rationale": "Wrong platform.", "search_angle": "core_topic"}
        ]})
        with self.assertRaises(MalformedSearchPlanOutput):
            SearchPlanGenerator(invalid).generate(campaign)

    def test_live_provider_requires_environment_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SearchPlanProviderConfigurationError):
                EnvironmentLLMSearchPlanProvider()


if __name__ == "__main__":
    unittest.main()
