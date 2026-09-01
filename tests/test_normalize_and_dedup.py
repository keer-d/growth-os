from pathlib import Path
import unittest

from pipeline.dedup import deduplicate_creators
from pipeline.normalize import normalize_profile_url
from pipeline.read_creators import load_creators


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "controlled_demo_minimal.json"


class NormalizeAndDedupTests(unittest.TestCase):
    def test_instagram_normalization_removes_query_case_and_trailing_slash(self):
        value = normalize_profile_url(
            "https://instagram.com/DEMO_NAME/?utm_source=test#top", "instagram"
        )
        self.assertEqual(value, "https://www.instagram.com/demo_name")

    def test_x_and_twitter_normalize_to_one_x_profile(self):
        self.assertEqual(
            normalize_profile_url("https://twitter.com/Demo_Name/", "x"),
            "https://x.com/demo_name",
        )
        self.assertEqual(
            normalize_profile_url("https://x.com/demo_name?ref=test", "x"),
            "https://x.com/demo_name",
        )

    def test_content_urls_are_not_guessed_into_profiles(self):
        with self.assertRaises(ValueError):
            normalize_profile_url("https://x.com/demo_name/status/123", "x")
        with self.assertRaises(ValueError):
            normalize_profile_url("https://instagram.com/p/post_id", "instagram")

    def test_same_platform_duplicates_but_cross_platform_does_not_merge(self):
        creators = load_creators(FIXTURE)
        result = deduplicate_creators(creators)
        self.assertEqual(len(result.new_records), 10)
        self.assertEqual(len(result.duplicate_records), 2)
        self.assertEqual(
            {item.record.record_id for item in result.duplicate_records},
            {"creator_002", "creator_006"},
        )
        dual_records = [item for item in result.new_records if "demo_dual_maker" in item.profile_url]
        self.assertEqual({item.platform for item in dual_records}, {"instagram", "x"})
        self.assertTrue(all(item.record.query_id for item in result.duplicate_records))


if __name__ == "__main__":
    unittest.main()
