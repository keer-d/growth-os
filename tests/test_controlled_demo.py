from pathlib import Path
import tempfile
import unittest

from pipeline.demo import DEFAULT_FIXTURE, run_controlled_demo
from storage.sqlite_store import SQLiteStore


class ControlledDemoTests(unittest.TestCase):
    def test_end_to_end_controlled_demo(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "demo.db"
            summary = run_controlled_demo(
                fixture_path=DEFAULT_FIXTURE,
                database_path=database,
                reset=True,
            )
            self.assertEqual(summary["retrieved"], 12)
            self.assertEqual(summary["duplicates"], 2)
            self.assertEqual(summary["new_creators"], 10)
            self.assertAlmostEqual(summary["new_creator_yield"], 10 / 12)
            self.assertEqual(
                summary["priority_counts"],
                {"P1": 4, "P2": 3, "P3": 1, "Needs Review": 2},
            )
            self.assertEqual(summary["reviews_stored"], 1)
            self.assertEqual(summary["feedback_stored"], 1)
            with SQLiteStore(database) as store:
                self.assertEqual(store.count("creators"), 10)
                self.assertEqual(store.count("creator_signals"), 10)
                self.assertEqual(store.count("audience_inferences"), 10)
                self.assertEqual(store.count("priority_decisions"), 10)
                self.assertEqual(store.count("queries"), 4)


if __name__ == "__main__":
    unittest.main()
