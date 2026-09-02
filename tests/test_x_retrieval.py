import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from pipeline.campaign_demo import load_campaign_briefs
from pipeline.search_plan_demo import run_reviewed_search_plan_demo
from pipeline.x_retrieval import (
    XAPIConfiguration,
    XLiveRetrievalAdapter,
    XProfileSearchProvider,
    XProviderConfigurationError,
    XProviderError,
    XRecentSearchProvider,
)


X_RESPONSE = {
    "data": [
        {
            "id": "1001",
            "author_id": "501",
            "text": "Building a portfolio website with AI tools.",
            "created_at": "2026-08-25T10:00:00.000Z",
        },
        {
            "id": "1002",
            "author_id": "501",
            "text": "Freelance web design workflow.",
            "created_at": "2026-08-26T10:00:00.000Z",
        },
    ],
    "includes": {
        "users": [
            {
                "id": "501",
                "username": "SyntheticXCreator",
                "name": "Synthetic X Creator",
                "description": "Designer teaching AI websites and portfolios.",
                "public_metrics": {"followers_count": 4321},
                "entities": {
                    "url": {
                        "urls": [
                            {"expanded_url": "https://synthetic-x.invalid/portfolio"}
                        ]
                    }
                },
            }
        ]
    },
    "meta": {"result_count": 2},
}


class MockXProvider(XProfileSearchProvider):
    connector_name = "mock_x_api"

    def __init__(self, response=None, error=None):
        self.response = {"meta": {"result_count": 0}} if response is None else response
        self.error = error
        self.calls = []

    def search(self, query_text, limit):
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


class XRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        brief = {
            item.campaign_id: item for item in load_campaign_briefs()
        }["campaign_demo_001"]
        _, _, _, cls.plan = run_reviewed_search_plan_demo(brief=brief)

    def test_only_approved_x_queries_execute_and_map_shared_contract(self):
        provider = MockXProvider(X_RESPONSE)
        result = XLiveRetrievalAdapter(provider, results_per_query=1).retrieve(
            self.plan, run_id="x_live_test"
        )
        approved_x = [query for query in self.plan.queries if query.platform == "x"]
        self.assertEqual([text for text, _ in provider.calls], [q.query_text for q in approved_x])
        self.assertEqual(len(result.query_results), len(approved_x))
        profile = result.query_results[0].profiles[0]
        self.assertEqual(profile.platform, "x")
        self.assertEqual(profile.profile_url, "https://x.com/SyntheticXCreator")
        self.assertEqual(profile.normalized_profile_url, "https://x.com/syntheticxcreator")
        self.assertEqual(profile.follower_count, 4321)
        self.assertEqual(len(profile.content_samples), 2)
        self.assertEqual(profile.query_id, approved_x[0].query_id)
        self.assertEqual(profile.source_query_id, approved_x[0].source_query_id)
        self.assertEqual(profile.campaign_id, self.plan.campaign_id)

    def test_zero_failure_and_malformed_responses_are_distinct(self):
        zero = XLiveRetrievalAdapter(MockXProvider()).retrieve(
            self.plan, run_id="x_zero", query_limit=1
        ).query_results[0]
        self.assertEqual(zero.status, "SUCCESS_ZERO_RESULTS")

        failed = XLiveRetrievalAdapter(
            MockXProvider(error=XProviderError("provider_timeout", "Synthetic timeout"))
        ).retrieve(self.plan, run_id="x_timeout", query_limit=1).query_results[0]
        self.assertEqual(failed.status, "FAILED")
        self.assertEqual(failed.error_code, "provider_timeout")

        malformed = XLiveRetrievalAdapter(
            MockXProvider({"data": [{"id": "1", "author_id": "2", "text": "x"}]})
        ).retrieve(self.plan, run_id="x_malformed", query_limit=1).query_results[0]
        self.assertEqual(malformed.status, "FAILED")
        self.assertEqual(malformed.error_code, "malformed_provider_response")

    def test_official_request_uses_header_approved_text_and_bounded_fields(self):
        provider = XRecentSearchProvider(
            XAPIConfiguration(bearer_token="test-x-token", timeout_seconds=30)
        )
        with patch(
            "pipeline.x_retrieval.urlopen", return_value=FakeHTTPResponse(X_RESPONSE)
        ) as mocked_open:
            provider.search("AI website creator", 1)
        request = mocked_open.call_args.args[0]
        params = parse_qs(urlparse(request.full_url).query)
        self.assertNotIn("test-x-token", request.full_url)
        self.assertEqual(request.get_header("Authorization"), "Bearer test-x-token")
        self.assertEqual(params["query"], ["AI website creator"])
        self.assertEqual(params["max_results"], ["10"])
        self.assertEqual(params["expansions"], ["author_id"])

    def test_missing_credential_is_explicit(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(XProviderConfigurationError) as context:
                XAPIConfiguration.from_environment()
        self.assertEqual(context.exception.error_code, "configuration_missing")


if __name__ == "__main__":
    unittest.main()
