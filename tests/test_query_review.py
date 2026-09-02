from collections import Counter
import unittest

from domain.query_review import QueryReviewAction
from pipeline.campaign_demo import load_campaign_briefs
from pipeline.query_review import (
    DuplicateFinalQueryError,
    HumanQueryReviewer,
    IncompleteQueryReviewError,
)
from pipeline.search_plan_demo import (
    run_reviewed_search_plan_demo,
    run_search_plan_demo,
    synthetic_review_actions,
)


class QueryReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brief = {
            brief.campaign_id: brief for brief in load_campaign_briefs()
        }["campaign_demo_001"]

    def draft_plan(self):
        _, plan = run_search_plan_demo(brief=self.brief)
        self.assertIsNotNone(plan)
        return plan

    def test_approve_reject_and_edit_create_expected_executable_plan(self):
        draft = self.draft_plan()
        review, approved = HumanQueryReviewer().review(
            draft,
            synthetic_review_actions(draft),
            completed_at="2026-08-15T10:00:09Z",
        )
        counts = Counter(item.decision for item in review.reviewed_queries)
        # The synthetic review pins 2 edits and 1 rejection to the first proposals
        # and approves the rest, so the shape holds as the proposer gains channels.
        self.assertEqual(counts["edited"], 2)
        self.assertEqual(counts["rejected"], 1)
        self.assertEqual(sum(counts.values()), len(draft.queries))
        self.assertEqual(len(approved.queries), len(draft.queries) - counts["rejected"])
        self.assertEqual(review.status, "complete")
        self.assertEqual(approved.status, "approved")

    def test_original_is_preserved_and_edited_text_enters_approved_plan(self):
        draft = self.draft_plan()
        review, approved = HumanQueryReviewer().review(
            draft,
            synthetic_review_actions(draft),
            completed_at="2026-08-15T10:00:09Z",
        )
        edited = next(item for item in review.reviewed_queries if item.decision == "edited")
        self.assertIn("sharing", edited.original_query.query_text)
        self.assertIn("teaching", edited.final_query_text)
        approved_copy = next(
            query
            for query in approved.queries
            if query.source_query_id == edited.original_query.query_id
        )
        self.assertEqual(approved_copy.query_text, edited.final_query_text)
        self.assertEqual(approved_copy.review_decision, "edited")

    def test_rejected_query_remains_in_review_but_not_approved_plan(self):
        draft = self.draft_plan()
        review, approved = HumanQueryReviewer().review(
            draft,
            synthetic_review_actions(draft),
            completed_at="2026-08-15T10:00:09Z",
        )
        rejected = next(item for item in review.reviewed_queries if item.decision == "rejected")
        self.assertIsNone(rejected.final_query_text)
        self.assertEqual(len(review.reviewed_queries), len(draft.queries))
        self.assertNotIn(
            rejected.original_query.query_id,
            {query.source_query_id for query in approved.queries},
        )

    def test_duplicate_final_query_text_is_rejected_explicitly(self):
        draft = self.draft_plan()
        actions = list(synthetic_review_actions(draft))
        actions[2] = QueryReviewAction(
            query_id=draft.queries[2].query_id,
            decision="edited",
            edited_query_text=draft.queries[0].query_text.upper(),
            human_comment="Synthetic duplicate.",
            reviewed_at="2026-08-15T10:00:03Z",
        )
        with self.assertRaises(DuplicateFinalQueryError):
            HumanQueryReviewer().review(draft, actions)

    def test_review_does_not_mutate_draft_plan(self):
        draft = self.draft_plan()
        before = draft.to_dict()
        HumanQueryReviewer().review(
            draft,
            synthetic_review_actions(draft),
            completed_at="2026-08-15T10:00:09Z",
        )
        self.assertEqual(draft.to_dict(), before)

    def test_incomplete_review_cannot_create_approved_plan(self):
        draft = self.draft_plan()
        incomplete_actions = synthetic_review_actions(draft)[:-1]
        with self.assertRaises(IncompleteQueryReviewError):
            HumanQueryReviewer().review(draft, incomplete_actions)

    def test_demo_counts_are_computed_from_real_review_output(self):
        _, draft, review, approved = run_reviewed_search_plan_demo(brief=self.brief)
        # Four channels are proposed for this campaign; one rejection is pinned.
        self.assertEqual(len(draft.queries), 14)
        self.assertEqual({query.platform for query in draft.queries},
                         {"instagram", "x", "youtube", "web"})
        self.assertEqual(len(review.reviewed_queries), len(draft.queries))
        self.assertEqual(len(approved.queries), len(draft.queries) - 1)


if __name__ == "__main__":
    unittest.main()
