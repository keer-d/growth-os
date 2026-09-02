from pathlib import Path
import tempfile
import unittest

from pipeline.campaign_demo import load_campaign_briefs
from pipeline.discovery import UnifiedDiscoveryRunner
from pipeline.instagram_retrieval import (
    InstagramLiveRetrievalAdapter,
    InstagramProfileSearchProvider,
    InstagramProviderError,
)
from pipeline.os_demo import run_os_demo
from pipeline.os_runner import execute_approved_plan, prepare_demo_campaign
from storage.sqlite_store import SQLiteStore


class MockInstagramProvider(InstagramProfileSearchProvider):
    connector_name = "mock_instagram"

    def __init__(self, error=None):
        self.error = error

    def search_profiles(self, query_text, limit):
        if self.error:
            raise self.error
        return []


class DiscoveryAndOSTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        brief = {
            item.campaign_id: item for item in load_campaign_briefs()
        }["campaign_demo_001"]
        cls.prepared = prepare_demo_campaign(brief)
        cls.plan = cls.prepared["approved_plan"]

    def test_controlled_runner_executes_only_approved_queries(self):
        result = UnifiedDiscoveryRunner().run(
            self.plan, mode="controlled", run_id="controlled_unified"
        )
        self.assertEqual(len(result.query_results), len(self.plan.queries))
        self.assertEqual({item.query_id for item in result.query_results}, {q.query_id for q in self.plan.queries})
        self.assertEqual(len(result.profiles), 12)
        # Controlled fixtures hold Instagram and X records only. YouTube and Web
        # queries must report a truthful zero result rather than fabricate one.
        by_channel = {}
        for item in result.query_results:
            by_channel.setdefault(item.platform, set()).add(item.status)
        self.assertEqual(by_channel["instagram"], {"SUCCESS_WITH_RESULTS"})
        self.assertEqual(by_channel["x"], {"SUCCESS_WITH_RESULTS"})
        self.assertEqual(by_channel["youtube"], {"SUCCESS_ZERO_RESULTS"})
        self.assertEqual(by_channel["web"], {"SUCCESS_ZERO_RESULTS"})
        self.assertTrue(all(not item.profiles for item in result.query_results
                            if item.platform in {"youtube", "web"}))

    def test_live_partial_failure_and_missing_provider_preserve_each_query(self):
        instagram = InstagramLiveRetrievalAdapter(
            MockInstagramProvider(
                InstagramProviderError("provider_timeout", "Synthetic timeout")
            )
        )
        runner = UnifiedDiscoveryRunner(instagram_adapter=instagram, x_adapter=None)
        result = runner.run(self.plan, mode="live", run_id="partial_live")
        instagram_results = [item for item in result.query_results if item.platform == "instagram"]
        x_results = [item for item in result.query_results if item.platform == "x"]
        self.assertTrue(all(item.status == "FAILED" for item in instagram_results))
        self.assertTrue(all(item.error_code == "provider_timeout" for item in instagram_results))
        self.assertTrue(all(item.status == "SKIPPED_NOT_CONFIGURED" for item in x_results))
        self.assertEqual(len(result.query_results), len(self.plan.queries))

    def test_controlled_end_to_end_persists_real_saturation_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "os.db"
            result = run_os_demo(
                mode="controlled", database_path=database, reset=True, runs=2
            )
            first, second = result["runs"]
            self.assertEqual((first["retrieved"], first["duplicates"], first["new_creators"]), (12, 2, 10))
            self.assertEqual((second["retrieved"], second["duplicates"], second["new_creators"]), (12, 12, 0))
            self.assertEqual(first["priority_counts"], {"P1": 4, "P2": 3, "P3": 1, "Needs Review": 2})
            with SQLiteStore(database) as store:
                self.assertEqual(store.count("runs"), 2)
                self.assertEqual(store.count("query_executions"), 26)
                self.assertEqual(store.count("creators"), 10)
                evidence = store.get_saturation_evidence()
                self.assertEqual(len(evidence), 26)
                self.assertIn(0.0, {row["new_creator_yield"] for row in evidence})

    def test_failed_and_skipped_queries_store_null_yield(self):
        instagram = InstagramLiveRetrievalAdapter(
            MockInstagramProvider(
                InstagramProviderError("provider_timeout", "Synthetic timeout")
            )
        )
        runner = UnifiedDiscoveryRunner(instagram_adapter=instagram, x_adapter=None)
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "failure.db"
            summary = execute_approved_plan(
                self.plan,
                mode="live",
                database_path=database,
                discovery_runner=runner,
            )
            self.assertEqual(summary["run_status"], "COMPLETED_WITH_ISSUES")
            with SQLiteStore(database) as store:
                rows = store.get_query_execution_history()
                self.assertEqual(len(rows), len(self.plan.queries))
                self.assertTrue(all(row["new_creator_yield"] is None for row in rows))
                self.assertIn("FAILED", {row["execution_status"] for row in rows})
                self.assertIn("SKIPPED_NOT_CONFIGURED", {row["execution_status"] for row in rows})


if __name__ == "__main__":
    unittest.main()
