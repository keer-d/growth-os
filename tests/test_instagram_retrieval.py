import json
from io import BytesIO
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from domain.query_review import QueryReviewAction
from pipeline.audience import DeterministicAudienceProvider
from pipeline.campaign_demo import load_campaign_briefs
from pipeline.dedup import deduplicate_creators
from pipeline.history import build_query_history
from pipeline.instagram_retrieval import (
    ApifyInstagramConfiguration,
    ApifyInstagramSearchProvider,
    InstagramLiveRetrievalAdapter,
    InstagramProfileSearchProvider,
    InstagramProviderConfigurationError,
    InstagramProviderError,
)
from pipeline.prioritize import prioritize_creator
from pipeline.query_review import HumanQueryReviewer
from pipeline.search_plan_demo import (
    run_reviewed_search_plan_demo,
    run_search_plan_demo,
    synthetic_review_actions,
)
from pipeline.signals import extract_signals
from storage.sqlite_store import SQLiteStore


PROFILE_ROW = {
    "id": "synthetic-provider-id",
    "username": "Synthetic.Design.Creator",
    "url": "https://www.instagram.com/Synthetic.Design.Creator/",
    "fullName": "Synthetic Design Creator",
    "biography": "US web designer sharing AI portfolio and no-code tutorials.",
    "followersCount": 12345,
    "externalUrls": [
        {"url": "https://synthetic-creator.invalid/portfolio"},
        {"url": ""},
    ],
    "externalUrl": "https://synthetic-creator.invalid/portfolio",
    "latestPosts": [
        {
            "caption": "Building a portfolio website with AI and no-code tools.",
            "url": "https://www.instagram.com/p/SYNTHETIC1/",
            "timestamp": "2026-08-20T10:00:00.000Z",
        },
        {
            "caption": "Freelance web design workflow for personal websites.",
            "url": "https://www.instagram.com/p/SYNTHETIC2/",
            "timestamp": "2026-08-25T10:00:00.000Z",
        },
    ],
}


class MockInstagramProvider(InstagramProfileSearchProvider):
    connector_name = "mock_apify_instagram"

    def __init__(self, response=None, error=None):
        self.response = [] if response is None else response
        self.error = error
        self.calls = []

    def search_profiles(self, query_text, limit):
        self.calls.append((query_text, limit))
        if self.error:
            raise self.error
        return self.response


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class InstagramRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brief = {
            brief.campaign_id: brief for brief in load_campaign_briefs()
        }["campaign_demo_001"]

    def approved_plan(self):
        _, _, _, approved = run_reviewed_search_plan_demo(brief=self.brief)
        self.assertIsNotNone(approved)
        return approved

    def test_only_approved_instagram_queries_execute(self):
        plan = self.approved_plan()
        provider = MockInstagramProvider([])
        result = InstagramLiveRetrievalAdapter(provider).retrieve(
            plan, run_id="live_run_001"
        )
        approved_instagram = [query for query in plan.queries if query.platform == "instagram"]
        self.assertEqual([text for text, _ in provider.calls], [
            query.query_text for query in approved_instagram
        ])
        self.assertEqual(len(result.query_results), len(approved_instagram))
        self.assertTrue(all("portfolio building challenges" not in text for text, _ in provider.calls))

    def test_rejected_instagram_query_and_draft_plan_cannot_execute(self):
        _, draft = run_search_plan_demo(brief=self.brief)
        actions = list(synthetic_review_actions(draft))
        actions[0] = QueryReviewAction(
            query_id=draft.queries[0].query_id,
            decision="rejected",
            human_comment="Synthetic rejection.",
            reviewed_at="2026-08-15T10:00:01Z",
        )
        actions[5] = QueryReviewAction(
            query_id=draft.queries[5].query_id,
            decision="approved",
            reviewed_at="2026-08-15T10:00:06Z",
        )
        _, approved = HumanQueryReviewer().review(
            draft, actions, completed_at="2026-08-15T10:00:09Z"
        )
        provider = MockInstagramProvider([])
        InstagramLiveRetrievalAdapter(provider).retrieve(
            approved, run_id="live_run_rejected"
        )
        self.assertNotIn(draft.queries[0].query_text, [text for text, _ in provider.calls])
        with self.assertRaises(TypeError):
            InstagramLiveRetrievalAdapter(provider).retrieve(
                draft, run_id="invalid_draft_run"
            )

    def test_provider_payload_maps_to_raw_profile_with_full_provenance(self):
        plan = self.approved_plan()
        provider = MockInstagramProvider([PROFILE_ROW])
        result = InstagramLiveRetrievalAdapter(provider, results_per_query=1).retrieve(
            plan, run_id="live_run_mapping", query_limit=1
        )
        query_result = result.query_results[0]
        profile = query_result.profiles[0]
        approved_query = next(query for query in plan.queries if query.platform == "instagram")

        self.assertEqual(query_result.status, "succeeded")
        self.assertEqual(profile.platform, "instagram")
        self.assertEqual(profile.profile_url, PROFILE_ROW["url"])
        self.assertEqual(
            profile.normalized_profile_url,
            "https://www.instagram.com/synthetic.design.creator",
        )
        self.assertEqual(profile.display_name, "Synthetic Design Creator")
        self.assertEqual(profile.follower_count, 12345)
        self.assertEqual(len(profile.external_urls), 1)
        self.assertEqual(len(profile.content_samples), 2)
        self.assertEqual(profile.discovery_mode, "live_instagram")
        self.assertEqual(profile.campaign_id, plan.campaign_id)
        self.assertEqual(profile.approved_search_plan_id, plan.approved_search_plan_id)
        self.assertEqual(profile.query_id, approved_query.query_id)
        self.assertEqual(profile.source_query_id, approved_query.source_query_id)
        self.assertEqual(profile.query_text, approved_query.query_text)
        self.assertEqual(profile.search_angle, approved_query.search_angle)
        self.assertEqual(profile.run_id, "live_run_mapping")

    def test_same_creator_keeps_each_query_provenance_before_dedup(self):
        plan = self.approved_plan()
        provider = MockInstagramProvider([PROFILE_ROW])
        result = InstagramLiveRetrievalAdapter(provider, results_per_query=1).retrieve(
            plan, run_id="live_run_multi_query", query_limit=2
        )
        self.assertEqual(len(result.profiles), 2)
        self.assertEqual(len({profile.query_id for profile in result.profiles}), 2)
        deduped = deduplicate_creators(result.profiles)
        self.assertEqual(len(deduped.new_records), 1)
        self.assertEqual(len(deduped.duplicate_records), 1)
        self.assertNotEqual(
            deduped.new_records[0].query_id,
            deduped.duplicate_records[0].record.query_id,
        )

    def test_missing_optional_fields_map_to_nullable_or_empty_values(self):
        provider = MockInstagramProvider([{"url": "https://www.instagram.com/minimal.profile"}])
        result = InstagramLiveRetrievalAdapter(provider).retrieve(
            self.approved_plan(), run_id="live_run_minimal", query_limit=1
        )
        profile = result.profiles[0]
        self.assertIsNone(profile.display_name)
        self.assertIsNone(profile.bio_text)
        self.assertIsNone(profile.follower_count)
        self.assertEqual(profile.external_urls, ())
        self.assertEqual(profile.content_samples, ())

    def test_zero_results_is_success_but_provider_failure_is_not(self):
        plan = self.approved_plan()
        zero = InstagramLiveRetrievalAdapter(MockInstagramProvider([])).retrieve(
            plan, run_id="live_run_zero", query_limit=1
        ).query_results[0]
        self.assertEqual(zero.status, "succeeded")
        self.assertEqual(zero.provider_result_count, 0)
        self.assertEqual(zero.profiles, ())
        self.assertIsNone(zero.error_code)

        failure_provider = MockInstagramProvider(
            error=InstagramProviderError("provider_timeout", "Synthetic timeout")
        )
        failed = InstagramLiveRetrievalAdapter(failure_provider).retrieve(
            plan, run_id="live_run_failed", query_limit=1
        ).query_results[0]
        self.assertEqual(failed.status, "failed")
        self.assertEqual(failed.error_code, "provider_timeout")
        self.assertTrue(failed.error_message)

    def test_malformed_and_non_profile_results_fail_explicitly(self):
        plan = self.approved_plan()
        malformed_provider = MockInstagramProvider({"not": "an array"})
        malformed = InstagramLiveRetrievalAdapter(malformed_provider).retrieve(
            plan, run_id="live_run_malformed", query_limit=1
        ).query_results[0]
        self.assertEqual(malformed.status, "failed")
        self.assertEqual(malformed.error_code, "malformed_provider_response")

        invalid_provider = MockInstagramProvider([
            {"url": "https://www.instagram.com/p/not-a-profile/"}
        ])
        invalid = InstagramLiveRetrievalAdapter(invalid_provider).retrieve(
            plan, run_id="live_run_invalid", query_limit=1
        ).query_results[0]
        self.assertEqual(invalid.status, "failed")
        self.assertEqual(invalid.error_code, "invalid_creator_record")
        self.assertEqual(invalid.invalid_result_count, 1)
        self.assertTrue(invalid.invalid_result_reasons)

    def test_apify_no_items_sentinel_is_a_successful_zero_result(self):
        configuration = ApifyInstagramConfiguration(api_token="test-token")
        provider = ApifyInstagramSearchProvider(configuration)
        with patch(
            "pipeline.instagram_retrieval.urlopen",
            return_value=FakeHTTPResponse(
                [{"error": "no_items", "errorDescription": "Synthetic empty input"}]
            ),
        ):
            self.assertEqual(provider.search_profiles("AI web design creator", 1), [])

    def test_apify_request_uses_safe_header_and_bounded_profile_search_payload(self):
        configuration = ApifyInstagramConfiguration(
            api_token="test-token",
            timeout_seconds=60,
            max_total_charge_usd=0.10,
        )
        provider = ApifyInstagramSearchProvider(configuration)
        with patch(
            "pipeline.instagram_retrieval.urlopen",
            return_value=FakeHTTPResponse([PROFILE_ROW]),
        ) as mocked_open:
            rows = provider.search_profiles("AI web design creator", 1)
        request = mocked_open.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(rows, [PROFILE_ROW])
        self.assertNotIn("test-token", request.full_url)
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
        self.assertEqual(payload["search"], "AI web design creator")
        self.assertEqual(payload["searchType"], "user")
        self.assertEqual(payload["searchLimit"], 1)
        self.assertFalse(payload["enhanceUserSearchWithFacebookPage"])
        self.assertIn("maxTotalChargeUsd=0.1", request.full_url)

    def test_missing_credential_is_explicit_and_no_live_request_occurs(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(InstagramProviderConfigurationError) as context:
                ApifyInstagramConfiguration.from_environment()
        self.assertEqual(context.exception.error_code, "missing_api_credential")

    def test_apify_http_failures_are_classified_without_exposing_response_data(self):
        cases = (
            (401, {"error": {"type": "invalid-token"}}, "provider_authentication_failure"),
            (408, {"error": {"type": "run-timeout-exceeded"}}, "provider_timeout"),
            (429, {"error": {"type": "rate-limit-exceeded"}}, "provider_rate_limit_or_quota"),
        )
        for status, payload, expected_code in cases:
            with self.subTest(status=status):
                error = HTTPError(
                    "https://api.apify.com/synthetic",
                    status,
                    "Synthetic error",
                    {},
                    BytesIO(json.dumps(payload).encode("utf-8")),
                )
                classified = ApifyInstagramSearchProvider._http_error(error)
                self.assertEqual(classified.error_code, expected_code)
                self.assertNotIn("invalid-token", classified.safe_message)

    def test_mapped_profile_is_compatible_with_full_downstream_and_sqlite(self):
        plan = self.approved_plan()
        result = InstagramLiveRetrievalAdapter(
            MockInstagramProvider([PROFILE_ROW]), results_per_query=1
        ).retrieve(plan, run_id="live_run_downstream", query_limit=1)
        deduped = deduplicate_creators(result.profiles)
        profile = deduped.new_records[0]
        signals = extract_signals(profile)
        inference = DeterministicAudienceProvider().infer(profile, signals)
        decision = prioritize_creator(signals, inference)
        histories = build_query_history(
            result.profiles,
            deduped,
            {profile.query_id: profile.query_text},
        )
        self.assertTrue(decision.priority)
        self.assertEqual(histories[0].retrieved, 1)
        self.assertEqual(histories[0].query_text, profile.query_text)

        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "live-test.db"
            with SQLiteStore(database) as store:
                store.save_run(
                    run_id=profile.run_id,
                    discovery_mode="live_instagram",
                    started_at=result.query_results[0].started_at,
                    completed_at=result.query_results[0].completed_at,
                    retrieved=1,
                    duplicates=0,
                    new_creators=1,
                )
                store.save_query_history(histories[0])
                store.save_creator(profile)
                store.save_signals(signals)
                store.save_audience_inference(inference)
                store.save_priority_decision(decision)
                self.assertEqual(store.count("creators"), 1)
                self.assertEqual(store.count("queries"), 1)
                self.assertEqual(store.count("priority_decisions"), 1)


if __name__ == "__main__":
    unittest.main()
