from pathlib import Path
import tempfile
import unittest

from domain.models import Feedback, QueryHistory, Review, utc_now_iso
from pipeline.dedup import deduplicate_creators
from pipeline.history import build_query_history
from pipeline.read_creators import load_creators
from storage.sqlite_store import SQLiteStore


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "controlled_demo_minimal.json"


class HistoryAndStorageTests(unittest.TestCase):
    def test_query_history_and_zero_retrieved_yield(self):
        creators = load_creators(FIXTURE)
        result = deduplicate_creators(creators)
        histories = build_query_history(creators, result, {})
        self.assertEqual(sum(item.retrieved for item in histories), 12)
        self.assertEqual(sum(item.duplicates for item in histories), 2)
        self.assertEqual(sum(item.new_creators for item in histories), 10)
        empty = QueryHistory.from_counts(
            query_id="empty",
            run_id="run",
            source_connector="fixture",
            query_text="empty query",
            retrieved=0,
            duplicates=0,
            new_creators=0,
        )
        self.assertEqual(empty.new_creator_yield, 0.0)

    def test_review_and_feedback_round_trip(self):
        profile = load_creators(FIXTURE)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.db"
            with SQLiteStore(path) as store:
                store.save_creator(profile)
                review_id = store.add_review(
                    Review(
                        record_id=profile.record_id,
                        status="approve",
                        structured_reason="strong_public_evidence",
                        comment="Synthetic review.",
                        reviewed_at=utc_now_iso(),
                    )
                )
                feedback_id = store.add_feedback(
                    Feedback(
                        record_id=profile.record_id,
                        review_id=review_id,
                        feedback_type="useful",
                        comment="Store only; do not learn automatically.",
                        created_at=utc_now_iso(),
                    )
                )
                self.assertEqual(store.get_review(review_id)["status"], "approve")
                self.assertEqual(store.get_feedback(feedback_id)["feedback_type"], "useful")


if __name__ == "__main__":
    unittest.main()
