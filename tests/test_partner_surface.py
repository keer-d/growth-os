"""Coverage for the Partner Discovery product surface.

Three properties matter most here and each has an explicit regression test:
  1. a credential VALUE can never reach the browser,
  2. a channel with no stored records never reports a fabricated count,
  3. a priority reason shown to a person is never invented by the UI layer.
"""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import channels
from pipeline.campaign_demo import load_campaign_briefs
from pipeline.os_runner import execute_approved_plan, prepare_demo_campaign
from pipeline.partner_types import (
    PARTNER_TYPES,
    derive_partner_type,
    partner_type_counts,
    partner_type_label,
)
from pipeline.ui_service import CreatorDiscoveryUIService


SENTINEL = "SENTINEL_CREDENTIAL_VALUE_9f2a"


class ChannelRegistryTests(unittest.TestCase):
    def test_four_channels_in_product_order(self):
        self.assertEqual(channels.CHANNELS, ("instagram", "x", "youtube", "web"))

    def test_absent_credential_reports_not_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            status = channels.channel_status("youtube")
        self.assertFalse(status["configured"])
        self.assertEqual(status["status"], "not_configured")

    def test_present_credential_reports_connected(self):
        with patch.dict(os.environ, {"YOUTUBE_API_KEY": SENTINEL}, clear=True):
            status = channels.channel_status("youtube")
        self.assertTrue(status["configured"])
        self.assertEqual(status["status"], "connected")

    def test_channel_status_never_carries_the_credential_value(self):
        with patch.dict(
            os.environ,
            {
                "YOUTUBE_API_KEY": SENTINEL,
                "WEB_SEARCH_API_KEY": SENTINEL,
                "X_BEARER_TOKEN": SENTINEL,
                "APIFY_API_TOKEN": SENTINEL,
            },
            clear=True,
        ):
            serialized = json.dumps(channels.all_channel_status())
        # Names travel to the browser; values never do.
        self.assertNotIn(SENTINEL, serialized)
        self.assertIn("YOUTUBE_API_KEY", serialized)


class PartnerTypeTests(unittest.TestCase):
    BASE = {
        "platform": "instagram",
        "display_name": "Synthetic Partner",
        "bio_text": "Designer sharing portfolio work.",
        "follower_count": None,
        "discovery_mode": "live",
        "source_connector": "x_api_v2_recent_search",
    }

    def derive(self, **overrides):
        return derive_partner_type({**self.BASE, **overrides})

    def test_every_result_is_a_known_partner_type(self):
        for followers in (None, 0, 5_000, 50_000, 250_000):
            with self.subTest(followers=followers):
                self.assertIn(
                    self.derive(follower_count=followers)["partner_type"], PARTNER_TYPES
                )

    def test_follower_bands_map_to_expected_types(self):
        self.assertEqual(self.derive(follower_count=None)["partner_type"], "creator")
        self.assertEqual(
            self.derive(follower_count=5_000)["partner_type"], "micro_influencer"
        )
        self.assertEqual(
            self.derive(follower_count=50_000)["partner_type"], "influencer"
        )
        self.assertEqual(self.derive(follower_count=250_000)["partner_type"], "kol")

    def test_bio_keyword_overrides_the_follower_band(self):
        # A 250k account would otherwise be a KOL; the stated relationship wins.
        self.assertEqual(
            self.derive(
                bio_text="Use my discount code for 20% off", follower_count=250_000
            )["partner_type"],
            "affiliate",
        )
        self.assertEqual(
            self.derive(bio_text="Join our Discord community", follower_count=250_000)[
                "partner_type"
            ],
            "community",
        )
        self.assertEqual(
            self.derive(bio_text="Founder and consultant", follower_count=250_000)[
                "partner_type"
            ],
            "industry_expert",
        )

    def test_web_publication_reads_as_media(self):
        self.assertEqual(
            self.derive(platform="web", bio_text="A magazine covering design")[
                "partner_type"
            ],
            "media",
        )

    def test_controlled_demo_records_are_flagged_as_demo_metadata(self):
        self.assertEqual(
            self.derive(discovery_mode="controlled_demo")["confidence"], "demo"
        )
        self.assertEqual(self.derive(follower_count=5_000)["confidence"], "observed")

    def test_every_result_states_its_basis(self):
        self.assertTrue(self.derive(follower_count=5_000)["basis"].strip())

    def test_counts_sum_to_the_number_of_profiles(self):
        profiles = [
            {**self.BASE, "follower_count": count}
            for count in (None, 5_000, 50_000, 250_000)
        ]
        counts = partner_type_counts(profiles)
        self.assertEqual(sum(counts.values()), len(profiles))

    def test_labels_exist_in_both_languages(self):
        for partner_type in PARTNER_TYPES:
            with self.subTest(partner_type=partner_type):
                self.assertTrue(partner_type_label(partner_type, "en").strip())
                self.assertTrue(partner_type_label(partner_type, "zh").strip())


class PartnerPoolTests(unittest.TestCase):
    """Runs one real Controlled Demo into a throwaway database."""

    @classmethod
    def setUpClass(cls):
        cls._directory = tempfile.TemporaryDirectory()
        cls.database = Path(cls._directory.name) / "partner_surface.db"
        brief = {item.campaign_id: item for item in load_campaign_briefs()}[
            "campaign_demo_001"
        ]
        prepared = prepare_demo_campaign(brief)
        execute_approved_plan(
            prepared["approved_plan"],
            mode="controlled",
            database_path=cls.database,
            seed_controlled_review=False,
        )
        cls.service = CreatorDiscoveryUIService(cls.database)
        cls.snapshot = cls.service.bootstrap()

    @classmethod
    def tearDownClass(cls):
        cls._directory.cleanup()

    def test_empty_database_reports_no_latest_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            empty = CreatorDiscoveryUIService(Path(directory) / "empty.db").bootstrap()
        self.assertIsNone(empty["latest_discovery"])
        self.assertEqual(empty["partner_pool"]["total"], 0)

    def test_pool_total_matches_stored_partner_records(self):
        pool = self.snapshot["partner_pool"]
        self.assertEqual(pool["total"], len(self.snapshot["creators"]))

    def test_reviewed_and_unreviewed_reconcile_to_the_total(self):
        pool = self.snapshot["partner_pool"]
        self.assertEqual(pool["reviewed"] + pool["unreviewed"], pool["total"])

    def test_channel_counts_never_fabricate_records(self):
        counts = self.snapshot["partner_pool"]["channel_counts"]
        # All four channels are listed so the product model stays visible.
        self.assertEqual(set(counts), set(channels.CHANNELS))
        # Controlled fixtures hold Instagram and X records only, so YouTube and
        # Web must report a real zero rather than an invented count.
        self.assertEqual(counts["youtube"], 0)
        self.assertEqual(counts["web"], 0)
        self.assertEqual(
            counts["instagram"] + counts["x"], self.snapshot["partner_pool"]["total"]
        )

    def test_latest_discovery_is_a_plain_language_summary(self):
        latest = self.snapshot["latest_discovery"]
        self.assertIsNotNone(latest)
        self.assertEqual(
            latest["duplicates"] + latest["new_partners"], latest["retrieved"]
        )
        self.assertGreaterEqual(latest["new_partner_yield"], 0.0)
        self.assertLessEqual(latest["new_partner_yield"], 1.0)

    def test_workspace_lists_every_channel(self):
        listed = {row["channel"] for row in self.snapshot["workspace"]["channels"]}
        self.assertTrue(set(channels.CHANNELS).issubset(listed))

    def test_partner_rows_carry_type_and_channel(self):
        for partner in self.snapshot["creators"]:
            with self.subTest(record=partner["record_id"]):
                self.assertIn(partner["partner_type"], PARTNER_TYPES)
                self.assertEqual(partner["channel"], partner["platform"])
                self.assertIn(
                    partner["partner_type_confidence"], {"observed", "demo"}
                )


class PartnerEvidenceTests(PartnerPoolTests):
    def detail(self):
        return self.service.creator_detail(self.snapshot["creators"][0]["record_id"])

    def test_priority_summary_is_never_invented(self):
        for partner in self.snapshot["creators"]:
            detail = self.service.creator_detail(partner["record_id"])
            stored = detail["priority_decision"]["reasons"]
            summary = detail["priority_summary"]["reasons"]
            with self.subTest(record=partner["record_id"]):
                self.assertTrue(summary)
                for clause in summary:
                    # Each clause must be a literal prefix of a reason the
                    # backend already stored — shortened, never authored here.
                    self.assertTrue(
                        any(text.startswith(clause) for text in stored),
                        f"{clause!r} is not derived from {stored!r}",
                    )

    def test_priority_summary_reports_the_stored_priority(self):
        detail = self.detail()
        self.assertEqual(
            detail["priority_summary"]["priority"],
            detail["priority_decision"]["priority"],
        )

    def test_key_signals_cover_the_five_summary_cards(self):
        signals = {item["signal"] for item in self.detail()["key_signals"]}
        self.assertEqual(
            signals,
            {"activity", "relevance", "audience", "market", "actionability"},
        )

    def test_key_signals_keep_their_evidence_for_expansion(self):
        for item in self.detail()["key_signals"]:
            with self.subTest(signal=item["signal"]):
                self.assertIn("evidence", item)
                self.assertIsInstance(item["evidence"], list)
                self.assertTrue(item["summary"].strip())

    def test_content_preview_is_capped_at_three(self):
        for partner in self.snapshot["creators"]:
            detail = self.service.creator_detail(partner["record_id"])
            total = len(detail["observed_facts"]["content_samples"])
            with self.subTest(record=partner["record_id"]):
                self.assertEqual(detail["content_samples_preview"], min(3, total))

    def test_ai_audience_summary_keeps_evidence_behind_the_summary(self):
        summary = self.detail()["ai_audience_summary"]
        self.assertIn("likely_audience", summary)
        self.assertIn("confidence", summary)
        self.assertIn("evidence", summary)

    def test_detail_never_carries_a_credential_value(self):
        with patch.dict(
            os.environ,
            {"YOUTUBE_API_KEY": SENTINEL, "APIFY_API_TOKEN": SENTINEL},
            clear=True,
        ):
            blob = json.dumps(self.detail()) + json.dumps(self.service.bootstrap())
        self.assertNotIn(SENTINEL, blob)


class HumanReviewPersistenceTests(PartnerPoolTests):
    def test_human_decision_persists_and_moves_the_pool_counter(self):
        service = CreatorDiscoveryUIService(self.database)
        before = service.bootstrap()["partner_pool"]["reviewed"]
        record_id = self.snapshot["creators"][-1]["record_id"]
        service.submit_creator_review(
            record_id=record_id,
            status="approve",
            structured_reason="Strong evidence fit",
            comment="Synthetic reviewer note.",
        )
        detail = service.creator_detail(record_id)
        self.assertEqual(detail["human_decision"]["status"], "approve")
        self.assertEqual(
            detail["human_decision"]["structured_reason"], "Strong evidence fit"
        )
        after = service.bootstrap()["partner_pool"]["reviewed"]
        self.assertEqual(after, before + 1)


if __name__ == "__main__":
    unittest.main()
