"""Fake-provider coverage for the YouTube and Web channel connectors.

No test here makes a network call. Live credentials are not required and are
never read: every case drives an in-process fake provider, so the contract is
exercised without pretending a provider succeeded.
"""

import json
import os
import unittest
from unittest.mock import patch

from pipeline.campaign_demo import load_campaign_briefs
from pipeline.search_plan_demo import run_reviewed_search_plan_demo
from pipeline.web_retrieval import (
    WebLiveRetrievalAdapter,
    WebProviderConfigurationError,
    WebProviderError,
    WebSearchConfiguration,
    WebSearchProvider,
)
from pipeline.youtube_retrieval import (
    YouTubeAPIConfiguration,
    YouTubeChannelSearchProvider,
    YouTubeLiveRetrievalAdapter,
    YouTubeProviderConfigurationError,
    YouTubeProviderError,
)


# The YouTube provider performs search.list then channels.list internally and
# returns the channels.list payload, so a fake only needs to return that shape.
YOUTUBE_RESPONSE = {
    "items": [
        {
            "id": "UCsyntheticChannelAAA",
            "snippet": {
                "title": "Synthetic Design Channel",
                "description": "Tutorials on portfolios, web design and AI website tools.",
                "customUrl": "@syntheticdesign",
            },
            "statistics": {"subscriberCount": "48200"},
        },
        {
            "id": "UCsyntheticChannelBBB",
            "snippet": {
                "title": "Synthetic Freelance Channel",
                "description": "Freelancing walkthroughs for independent designers.",
            },
            "statistics": {"hiddenSubscriberCount": True},
        },
    ]
}

WEB_RESPONSE = {
    "items": [
        {
            "link": "https://synthetic-design-journal.invalid/portfolio-guide?utm_source=x",
            "title": "Synthetic Design Journal",
            "snippet": "A publication covering portfolios and freelance web design.",
        },
        {
            "link": "https://synthetic-expert.invalid/",
            "title": "Synthetic Expert",
            "snippet": "Consultant writing about AI website tools for designers.",
        },
    ]
}


class MockYouTubeProvider(YouTubeChannelSearchProvider):
    connector_name = "mock_youtube_api"

    def __init__(self, response=None, error=None):
        self.response = {"items": []} if response is None else response
        self.error = error
        self.calls = []

    def search(self, query_text, limit):
        self.calls.append((query_text, limit))
        if self.error:
            raise self.error
        return self.response


class MockWebProvider(WebSearchProvider):
    connector_name = "mock_web_search"

    def __init__(self, response=None, error=None):
        self.response = {"items": []} if response is None else response
        self.error = error
        self.calls = []

    def search(self, query_text, limit):
        self.calls.append((query_text, limit))
        if self.error:
            raise self.error
        return self.response


class ChannelConnectorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        brief = {item.campaign_id: item for item in load_campaign_briefs()}[
            "campaign_demo_001"
        ]
        _, _, _, cls.plan = run_reviewed_search_plan_demo(brief=brief)

    def approved(self, channel):
        return [query for query in self.plan.queries if query.platform == channel]

    def assert_counts_reconcile(self, result):
        """Every SUCCESS_* result must account for each provider record."""
        if result.status.startswith("SUCCESS_"):
            self.assertEqual(
                len(result.profiles) + result.invalid_result_count,
                result.provider_result_count,
            )
        self.assertEqual(
            len(result.invalid_result_reasons), result.invalid_result_count
        )


class YouTubeRetrievalTests(ChannelConnectorTestCase):
    def test_only_approved_youtube_queries_execute_and_map_shared_contract(self):
        provider = MockYouTubeProvider(YOUTUBE_RESPONSE)
        run = YouTubeLiveRetrievalAdapter(provider, results_per_query=2).retrieve(
            self.plan, run_id="youtube_live_test"
        )
        approved = self.approved("youtube")
        self.assertTrue(approved, "the demo plan must propose YouTube queries")
        self.assertEqual(
            [text for text, _ in provider.calls], [q.query_text for q in approved]
        )
        self.assertEqual(len(run.query_results), len(approved))

        first = run.query_results[0]
        self.assertEqual(first.status, "SUCCESS_WITH_RESULTS")
        self.assert_counts_reconcile(first)
        profile = first.profiles[0]
        self.assertEqual(profile.platform, "youtube")
        self.assertEqual(profile.discovery_mode, "live")
        self.assertEqual(profile.source_connector, "mock_youtube_api")
        self.assertEqual(profile.profile_url, "https://www.youtube.com/@syntheticdesign")
        self.assertEqual(
            profile.normalized_profile_url, "https://www.youtube.com/@syntheticdesign"
        )
        self.assertEqual(profile.follower_count, 48200)
        # Provenance must survive retrieval or the run is not auditable.
        self.assertEqual(profile.campaign_id, self.plan.campaign_id)
        self.assertEqual(profile.approved_search_plan_id, self.plan.approved_search_plan_id)
        self.assertEqual(profile.run_id, "youtube_live_test")
        self.assertEqual(profile.query_id, first.query_id)
        self.assertEqual(profile.query_text, first.query_text)
        self.assertEqual(profile.search_angle, first.search_angle)

    def test_channel_without_public_handle_falls_back_to_channel_id(self):
        provider = MockYouTubeProvider(YOUTUBE_RESPONSE)
        run = YouTubeLiveRetrievalAdapter(provider, results_per_query=2).retrieve(
            self.plan, run_id="youtube_fallback"
        )
        second = run.query_results[0].profiles[1]
        self.assertEqual(
            second.profile_url,
            "https://www.youtube.com/channel/UCsyntheticChannelBBB",
        )

    def test_hidden_subscriber_count_is_none_rather_than_zero(self):
        provider = MockYouTubeProvider(YOUTUBE_RESPONSE)
        run = YouTubeLiveRetrievalAdapter(provider, results_per_query=2).retrieve(
            self.plan, run_id="youtube_hidden"
        )
        hidden = run.query_results[0].profiles[1]
        # A hidden count is unknown, not zero — zero would be a fabricated fact.
        self.assertIsNone(hidden.follower_count)

    def test_empty_items_report_truthful_zero_results(self):
        provider = MockYouTubeProvider({"items": []})
        run = YouTubeLiveRetrievalAdapter(provider).retrieve(
            self.plan, run_id="youtube_zero"
        )
        for result in run.query_results:
            self.assertEqual(result.status, "SUCCESS_ZERO_RESULTS")
            self.assertEqual(result.provider_result_count, 0)
            self.assertEqual(result.profiles, ())
            self.assertIsNone(result.error_code)

    def test_invalid_channel_becomes_reason_without_losing_the_query(self):
        response = {
            "items": [
                {"id": "", "snippet": {"title": "Broken"}},
                YOUTUBE_RESPONSE["items"][0],
            ]
        }
        provider = MockYouTubeProvider(response)
        run = YouTubeLiveRetrievalAdapter(provider, results_per_query=2).retrieve(
            self.plan, run_id="youtube_invalid"
        )
        result = run.query_results[0]
        self.assertEqual(result.status, "SUCCESS_WITH_RESULTS")
        self.assertEqual(len(result.profiles), 1)
        self.assertEqual(result.invalid_result_count, 1)
        self.assert_counts_reconcile(result)

    def test_provider_error_becomes_failed_with_a_safe_code(self):
        provider = MockYouTubeProvider(
            error=YouTubeProviderError("provider_timeout", "Synthetic timeout")
        )
        run = YouTubeLiveRetrievalAdapter(provider).retrieve(
            self.plan, run_id="youtube_failed"
        )
        for result in run.query_results:
            self.assertEqual(result.status, "FAILED")
            self.assertEqual(result.error_code, "provider_timeout")
            self.assertTrue(result.error_message)
            self.assertEqual(result.profiles, ())

    def test_missing_credential_raises_configuration_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(YouTubeProviderConfigurationError) as caught:
                YouTubeAPIConfiguration.from_environment()
        self.assertEqual(caught.exception.error_code, "configuration_missing")

    def test_configuration_never_reveals_the_api_key(self):
        configuration = YouTubeAPIConfiguration(api_key="SENTINEL_YT_KEY")
        self.assertNotIn("SENTINEL_YT_KEY", repr(configuration))
        self.assertNotIn("SENTINEL_YT_KEY", str(configuration))


class WebRetrievalTests(ChannelConnectorTestCase):
    def test_only_approved_web_queries_execute_and_map_shared_contract(self):
        provider = MockWebProvider(WEB_RESPONSE)
        run = WebLiveRetrievalAdapter(provider, results_per_query=2).retrieve(
            self.plan, run_id="web_live_test"
        )
        approved = self.approved("web")
        self.assertTrue(approved, "the demo plan must propose Web queries")
        self.assertEqual(
            [text for text, _ in provider.calls], [q.query_text for q in approved]
        )

        first = run.query_results[0]
        self.assertEqual(first.status, "SUCCESS_WITH_RESULTS")
        self.assert_counts_reconcile(first)
        profile = first.profiles[0]
        self.assertEqual(profile.platform, "web")
        self.assertEqual(profile.discovery_mode, "live")
        # The observed URL is preserved verbatim; only the derived identity is canonical.
        self.assertEqual(
            profile.profile_url,
            "https://synthetic-design-journal.invalid/portfolio-guide?utm_source=x",
        )
        self.assertEqual(
            profile.normalized_profile_url,
            "https://synthetic-design-journal.invalid/portfolio-guide",
        )
        self.assertEqual(profile.campaign_id, self.plan.campaign_id)
        self.assertEqual(profile.run_id, "web_live_test")

    def test_web_partners_never_carry_a_fabricated_follower_count(self):
        provider = MockWebProvider(WEB_RESPONSE)
        run = WebLiveRetrievalAdapter(provider, results_per_query=2).retrieve(
            self.plan, run_id="web_followers"
        )
        for profile in run.query_results[0].profiles:
            # The web has no follower concept. None is the only honest value.
            self.assertIsNone(profile.follower_count)

    def test_social_link_is_rejected_so_one_partner_is_not_counted_twice(self):
        response = {
            "items": [
                {
                    "link": "https://www.instagram.com/synthetic_creator",
                    "title": "Synthetic on Instagram",
                    "snippet": "Instagram profile.",
                },
                WEB_RESPONSE["items"][1],
            ]
        }
        provider = MockWebProvider(response)
        run = WebLiveRetrievalAdapter(provider, results_per_query=2).retrieve(
            self.plan, run_id="web_crosschannel"
        )
        result = run.query_results[0]
        self.assertEqual(len(result.profiles), 1)
        self.assertEqual(result.invalid_result_count, 1)
        self.assert_counts_reconcile(result)
        self.assertNotIn(
            "instagram.com",
            " ".join(profile.profile_url for profile in result.profiles),
        )

    def test_alternate_vendor_envelopes_are_accepted(self):
        for key in ("results", "organic_results"):
            with self.subTest(envelope=key):
                provider = MockWebProvider({key: WEB_RESPONSE["items"]})
                run = WebLiveRetrievalAdapter(provider, results_per_query=2).retrieve(
                    self.plan, run_id=f"web_{key}"
                )
                self.assertEqual(run.query_results[0].status, "SUCCESS_WITH_RESULTS")

    def test_empty_results_report_truthful_zero_results(self):
        provider = MockWebProvider({"items": []})
        run = WebLiveRetrievalAdapter(provider).retrieve(self.plan, run_id="web_zero")
        for result in run.query_results:
            self.assertEqual(result.status, "SUCCESS_ZERO_RESULTS")
            self.assertEqual(result.provider_result_count, 0)
            self.assertIsNone(result.error_code)

    def test_provider_error_becomes_failed_with_a_safe_code(self):
        provider = MockWebProvider(
            error=WebProviderError("provider_rate_limit_or_quota", "Synthetic quota")
        )
        run = WebLiveRetrievalAdapter(provider).retrieve(self.plan, run_id="web_failed")
        for result in run.query_results:
            self.assertEqual(result.status, "FAILED")
            self.assertEqual(result.error_code, "provider_rate_limit_or_quota")
            self.assertEqual(result.profiles, ())

    def test_missing_credential_raises_configuration_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(WebProviderConfigurationError) as caught:
                WebSearchConfiguration.from_environment()
        self.assertEqual(caught.exception.error_code, "configuration_missing")

    def test_configuration_never_reveals_the_api_key(self):
        configuration = WebSearchConfiguration(api_key="SENTINEL_WEB_KEY")
        self.assertNotIn("SENTINEL_WEB_KEY", repr(configuration))
        self.assertNotIn("SENTINEL_WEB_KEY", str(configuration))


if __name__ == "__main__":
    unittest.main()
