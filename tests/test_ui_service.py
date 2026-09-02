import http.client
import json
import os
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch

from pipeline.ui_server import build_server
from pipeline.ui_service import CreatorDiscoveryUIService, UIServiceError


COMPLETE_BRIEF = (
    "I want active creators in the US and Canada who create content around "
    "web design, portfolios, freelancing and AI website tools. Their audiences "
    "should ideally include designers and freelancers."
)


class UIServiceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.directory.name) / "ui.db"
        self.service = CreatorDiscoveryUIService(self.database_path)

    def tearDown(self):
        self.directory.cleanup()

    def _approved_actions(self, workflow):
        return [
            {"query_id": query["query_id"], "decision": "approved"}
            for query in workflow["draft_search_plan"]["queries"]
        ]

    def test_real_campaign_and_draft_plan_are_exposed_without_overwriting_brief(self):
        workflow = self.service.generate_search_plan(COMPLETE_BRIEF)
        self.assertEqual(workflow["original_brief"], COMPLETE_BRIEF)
        self.assertEqual(workflow["campaign_parse"]["status"], "complete")
        self.assertEqual(workflow["draft_search_plan"]["status"], "draft")
        queries = workflow["draft_search_plan"]["queries"]
        self.assertEqual(len(queries), 14)
        self.assertEqual({query["platform"] for query in queries},
                         {"instagram", "x", "youtube", "web"})

    def test_incomplete_brief_returns_questions_and_no_draft(self):
        workflow = self.service.generate_search_plan("I want to find some creators.")
        self.assertIsNone(workflow["draft_search_plan"])
        self.assertEqual(workflow["campaign_parse"]["status"], "needs_clarification")
        self.assertTrue(workflow["campaign_parse"]["clarification_questions"])

    def test_controlled_execution_uses_reviewed_plan_and_populates_all_ui_layers(self):
        workflow = self.service.generate_search_plan(COMPLETE_BRIEF)
        result = self.service.run_discovery(
            workflow_id=workflow["workflow_id"],
            actions=self._approved_actions(workflow),
            mode="controlled",
        )
        self.assertEqual(result["run_summary"]["retrieved"], 12)
        self.assertEqual(result["run_summary"]["new_creators"], 10)
        self.assertEqual(len(result["approved_search_plan"]["queries"]), 14)

        snapshot = self.service.bootstrap()
        self.assertEqual(snapshot["overview"]["total_creators"], 10)
        self.assertEqual(len(snapshot["runs"]), 1)
        detail = self.service.creator_detail(snapshot["creators"][0]["record_id"])
        self.assertIsNotNone(detail["derived_signals"])
        self.assertIsNotNone(detail["ai_audience_inference"])
        self.assertIsNotNone(detail["priority_decision"])

    def test_live_execution_requires_explicit_confirmation_before_provider_calls(self):
        workflow = self.service.generate_search_plan(COMPLETE_BRIEF)
        with self.assertRaisesRegex(UIServiceError, "explicit confirmation"):
            self.service.run_discovery(
                workflow_id=workflow["workflow_id"],
                actions=self._approved_actions(workflow),
                mode="live",
                confirm_live=False,
            )
        self.assertEqual(self.service.bootstrap()["runs"], [])

    def test_creator_review_is_stored_and_returned_as_human_decision(self):
        workflow = self.service.generate_search_plan(COMPLETE_BRIEF)
        self.service.run_discovery(
            workflow_id=workflow["workflow_id"],
            actions=self._approved_actions(workflow),
            mode="controlled",
        )
        record_id = self.service.bootstrap()["creators"][0]["record_id"]
        stored = self.service.submit_creator_review(
            record_id=record_id,
            status="approve",
            structured_reason="strong_campaign_fit",
            comment="Clear fit for the campaign.",
        )
        detail = self.service.creator_detail(record_id)
        self.assertEqual(stored["status"], "approve")
        self.assertEqual(detail["human_decision"]["structured_reason"], "strong_campaign_fit")

    def test_provider_status_never_returns_credential_values(self):
        with patch.dict(
            os.environ,
            {"APIFY_API_TOKEN": "secret-instagram-token", "X_BEARER_TOKEN": "secret-x-token"},
        ):
            serialized = json.dumps(self.service.bootstrap())
        self.assertNotIn("secret-instagram-token", serialized)
        self.assertNotIn("secret-x-token", serialized)
        providers = json.loads(serialized)["workspace"]["providers"]
        self.assertTrue(providers["instagram"]["configured"])
        self.assertTrue(providers["x"]["configured"])


class UIServerTests(unittest.TestCase):
    def test_local_server_serves_ui_and_health_without_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            server = build_server(
                host="127.0.0.1",
                port=0,
                database_path=Path(directory) / "ui.db",
            )
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                connection = http.client.HTTPConnection(
                    "127.0.0.1", server.server_address[1], timeout=5
                )
                connection.request("GET", "/")
                response = connection.getresponse()
                html = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
                self.assertIn("Growth OS", html)

                connection.request("GET", "/api/health")
                response = connection.getresponse()
                health = json.loads(response.read())
                self.assertEqual(health, {"status": "ok"})
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
