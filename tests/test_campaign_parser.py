import os
import unittest
from unittest.mock import patch

from domain.campaign import CampaignBrief
from pipeline.campaign_demo import load_campaign_briefs
from pipeline.campaign_parser import (
    CampaignBriefParser,
    CampaignParserProvider,
    CampaignProviderConfigurationError,
    DeterministicCampaignProvider,
    EnvironmentLLMCampaignProvider,
)


class MalformedProvider(CampaignParserProvider):
    provider_name = "malformed-test"
    model_name = "malformed-test-model"

    def generate(self, brief: CampaignBrief) -> str:
        return "this is not valid JSON"


class MissingMarketKeyProvider(CampaignParserProvider):
    provider_name = "missing-key-test"
    model_name = "missing-key-test-model"

    def generate(self, brief: CampaignBrief) -> str:
        return """{
          "goal": "Discover creators for partnerships",
          "content_themes": ["web design"],
          "target_audience": ["designers"],
          "exclusions": []
        }"""


class CampaignParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = {item.campaign_id: item for item in load_campaign_briefs()}

    def parse_fixture(self, campaign_id):
        brief = self.fixtures[campaign_id]
        return CampaignBriefParser(DeterministicCampaignProvider()).parse(brief)

    def test_successful_offline_parse_with_original_brief_preserved(self):
        brief = self.fixtures["campaign_demo_001"]
        with patch.dict(os.environ, {}, clear=True):
            result = CampaignBriefParser(DeterministicCampaignProvider()).parse(brief)
        self.assertEqual(result.status, "complete")
        self.assertEqual(result.brief.original_brief, brief.original_brief)
        self.assertEqual(result.provenance.provider, "mock")
        self.assertEqual(result.definition.campaign_id, brief.campaign_id)

    def test_multiple_markets_themes_and_audiences(self):
        first = self.parse_fixture("campaign_demo_001").definition
        second = self.parse_fixture("campaign_demo_002").definition
        self.assertEqual(first.target_markets, ("United States", "Canada"))
        self.assertIn("AI website tools", first.content_themes)
        self.assertIn("portfolio building", first.content_themes)
        self.assertEqual(first.target_audience, ("designers", "freelancers"))
        self.assertEqual(second.target_markets, ("United Kingdom", "Ireland"))
        self.assertIn("no-code", second.content_themes)
        self.assertIn("web design", second.content_themes)

    def test_missing_market_returns_incomplete_without_invention(self):
        result = self.parse_fixture("campaign_demo_003")
        self.assertEqual(result.status, "incomplete")
        self.assertEqual(result.definition.target_markets, ())
        self.assertEqual(result.missing_required_fields, ("target_markets",))
        self.assertTrue(result.clarification_questions)

    def test_explicit_exclusions_are_preserved(self):
        result = self.parse_fixture("campaign_demo_004")
        self.assertEqual(result.status, "complete")
        self.assertEqual(result.definition.exclusions, ("agencies", "corporate brand accounts"))

    def test_vague_brief_requires_clarification(self):
        result = self.parse_fixture("campaign_demo_005")
        self.assertEqual(result.status, "needs_clarification")
        self.assertEqual(
            set(result.missing_required_fields),
            {"target_markets", "content_themes", "target_audience"},
        )
        self.assertEqual(len(result.clarification_questions), 3)

    def test_malformed_provider_output_is_an_explicit_failure(self):
        brief = self.fixtures["campaign_demo_001"]
        result = CampaignBriefParser(MalformedProvider()).parse(brief)
        self.assertEqual(result.status, "failed")
        self.assertIsNone(result.definition)
        self.assertEqual(result.error_code, "malformed_provider_output")
        self.assertEqual(result.brief.original_brief, brief.original_brief)

    def test_omitted_required_key_is_incomplete_not_malformed(self):
        brief = self.fixtures["campaign_demo_001"]
        result = CampaignBriefParser(MissingMarketKeyProvider()).parse(brief)
        self.assertEqual(result.status, "incomplete")
        self.assertEqual(result.definition.target_markets, ())
        self.assertEqual(result.missing_required_fields, ("target_markets",))

    def test_live_provider_requires_environment_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(CampaignProviderConfigurationError):
                EnvironmentLLMCampaignProvider()


if __name__ == "__main__":
    unittest.main()
