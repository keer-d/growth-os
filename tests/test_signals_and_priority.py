from dataclasses import replace
from pathlib import Path
import unittest

from domain.models import ContentSample
from pipeline.audience import DeterministicAudienceProvider
from pipeline.prioritize import prioritize_creator
from pipeline.read_creators import load_creators
from pipeline.signals import extract_signals


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "signal_policy_cases.json"


class SignalsAndPriorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = {item.record_id: item for item in load_creators(FIXTURE)}
        cls.provider = DeterministicAudienceProvider()

    def decision(self, record_id):
        profile = self.profiles[record_id]
        signals = extract_signals(profile)
        inference = self.provider.infer(profile, signals)
        return signals, inference, prioritize_creator(signals, inference)

    def test_signals_keep_human_readable_reasons_and_evidence(self):
        signals, inference, _ = self.decision("creator_001")
        self.assertEqual(signals.activity.value, "high")
        self.assertEqual(signals.content_relevance.value, "high")
        self.assertTrue(signals.activity.reason)
        self.assertTrue(signals.content_relevance.evidence)
        self.assertEqual(inference.provider, "mock")
        self.assertNotIn("good", " ".join(inference.likely_audience).lower())

    def test_small_relevant_creator_can_outrank_large_weak_creator(self):
        _, _, small = self.decision("creator_005")
        _, _, large = self.decision("creator_004")
        self.assertEqual(small.priority, "P1")
        self.assertEqual(large.priority, "P3")

    def test_activity_can_raise_moderate_relevance(self):
        profile = self.profiles["creator_003"]
        active_signals = extract_signals(profile)
        active_inference = self.provider.infer(profile, active_signals)
        active_decision = prioritize_creator(active_signals, active_inference)

        old_profile = replace(
            profile,
            content_samples=tuple(
                ContentSample(sample.text, sample.url, "2025-01-01T12:00:00Z")
                for sample in profile.content_samples
            ),
        )
        old_signals = extract_signals(old_profile)
        old_inference = self.provider.infer(old_profile, old_signals)
        old_decision = prioritize_creator(old_signals, old_inference)

        self.assertEqual(active_signals.content_relevance.value, "moderate")
        self.assertEqual(active_signals.activity.value, "high")
        self.assertEqual(old_signals.activity.value, "low")
        self.assertEqual(active_decision.priority, "P2")
        self.assertEqual(old_decision.priority, "P3")

    def test_missing_contact_does_not_penalize_relevant_creator(self):
        signals, _, decision = self.decision("creator_005")
        self.assertEqual(signals.actionability.value, "missing")
        self.assertEqual(decision.priority, "P1")

    def test_old_or_outside_market_is_not_automatic_rejection(self):
        old_signals, _, old_decision = self.decision("creator_007")
        outside_signals, _, outside_decision = self.decision("creator_008")
        self.assertEqual(old_signals.activity.value, "low")
        self.assertEqual(old_decision.priority, "P2")
        self.assertEqual(outside_signals.market.value, "outside")
        self.assertEqual(outside_decision.priority, "P2")

    def test_conflicting_or_spam_evidence_needs_review(self):
        conflicting, _, conflict_decision = self.decision("creator_009")
        spam, _, spam_decision = self.decision("creator_010")
        self.assertEqual(conflicting.market.value, "conflicting")
        self.assertEqual(conflict_decision.priority, "Needs Review")
        self.assertEqual(spam.record_quality.value, "spam")
        self.assertEqual(spam_decision.priority, "Needs Review")


if __name__ == "__main__":
    unittest.main()
