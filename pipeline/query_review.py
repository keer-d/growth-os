"""Human-only review from Draft Search Plan to Approved Search Plan."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Iterable

from domain.models import utc_now_iso
from domain.query_review import (
    ApprovedSearchPlan,
    ApprovedSearchQuery,
    QueryReviewAction,
    ReviewedQuery,
    SearchPlanReview,
)
from domain.search_plan import DraftSearchPlan


class QueryReviewError(RuntimeError):
    """A human review could not be converted safely."""


class IncompleteQueryReviewError(QueryReviewError):
    """Not every Draft query received exactly one decision."""


class DuplicateFinalQueryError(QueryReviewError):
    """Two executable decisions resolve to the same final query text."""


class NoExecutableQueriesError(QueryReviewError):
    """A completed review rejected every Draft query."""


class HumanQueryReviewer:
    """Validates human decisions without changing or executing the Draft plan."""

    def review(
        self,
        draft_plan: DraftSearchPlan,
        actions: Iterable[QueryReviewAction],
        *,
        completed_at: str | None = None,
    ) -> tuple[SearchPlanReview, ApprovedSearchPlan]:
        if not isinstance(draft_plan, DraftSearchPlan) or draft_plan.status != "draft":
            raise IncompleteQueryReviewError(
                "only a complete DraftSearchPlan with status 'draft' can be reviewed"
            )

        actions_by_query_id: dict[str, QueryReviewAction] = {}
        for action in actions:
            if not isinstance(action, QueryReviewAction):
                raise QueryReviewError("every action must be a QueryReviewAction")
            if action.query_id in actions_by_query_id:
                raise IncompleteQueryReviewError(
                    f"Draft query {action.query_id} received more than one decision"
                )
            actions_by_query_id[action.query_id] = action

        expected_ids = {query.query_id for query in draft_plan.queries}
        submitted_ids = set(actions_by_query_id)
        if submitted_ids != expected_ids:
            missing = sorted(expected_ids - submitted_ids)
            unknown = sorted(submitted_ids - expected_ids)
            details = []
            if missing:
                details.append("missing decisions for: " + ", ".join(missing))
            if unknown:
                details.append("unknown query IDs: " + ", ".join(unknown))
            raise IncompleteQueryReviewError("; ".join(details))

        reviewed_queries = tuple(
            self._reviewed_query(query, actions_by_query_id[query.query_id])
            for query in draft_plan.queries
        )
        self._reject_duplicate_final_texts(reviewed_queries)

        completed_timestamp = completed_at or utc_now_iso()
        review_id = self._stable_id(
            "review",
            {
                "draft_search_plan_id": draft_plan.search_plan_id,
                "reviewed_queries": [item.to_dict() for item in reviewed_queries],
                "completed_at": completed_timestamp,
            },
        )
        review = SearchPlanReview(
            review_id=review_id,
            draft_search_plan_id=draft_plan.search_plan_id,
            campaign_id=draft_plan.campaign_id,
            status="complete",
            reviewed_queries=reviewed_queries,
            completed_at=completed_timestamp,
        )

        executable_reviews = [
            item for item in reviewed_queries if item.decision in {"approved", "edited"}
        ]
        if not executable_reviews:
            raise NoExecutableQueriesError(
                "all Draft queries were rejected; no Approved Search Plan was created"
            )
        approved_plan_id = self._stable_id(
            "approvedplan",
            {
                "review_id": review.review_id,
                "queries": [
                    {
                        "source_query_id": item.original_query.query_id,
                        "query_text": item.final_query_text,
                        "decision": item.decision,
                    }
                    for item in executable_reviews
                ],
            },
        )
        approved_queries = tuple(
            ApprovedSearchQuery(
                query_id=f"{approved_plan_id}_q{index:03d}",
                source_query_id=item.original_query.query_id,
                campaign_id=draft_plan.campaign_id,
                platform=item.original_query.platform,
                query_text=item.final_query_text or "",
                search_angle=item.original_query.search_angle,
                review_decision=item.decision,
            )
            for index, item in enumerate(executable_reviews, start=1)
        )
        approved_plan = ApprovedSearchPlan(
            approved_search_plan_id=approved_plan_id,
            source_draft_search_plan_id=draft_plan.search_plan_id,
            review_id=review.review_id,
            campaign_id=draft_plan.campaign_id,
            status="approved",
            queries=approved_queries,
            approved_at=completed_timestamp,
        )
        return review, approved_plan

    @staticmethod
    def _reviewed_query(query, action: QueryReviewAction) -> ReviewedQuery:
        if action.decision == "approved":
            final_query_text = query.query_text
        elif action.decision == "rejected":
            final_query_text = None
        else:
            final_query_text = " ".join((action.edited_query_text or "").split())
        return ReviewedQuery(
            original_query=query,
            final_query_text=final_query_text,
            decision=action.decision,
            human_comment=(
                action.human_comment.strip() if action.human_comment is not None else None
            ),
            reviewed_at=action.reviewed_at or utc_now_iso(),
        )

    @staticmethod
    def _reject_duplicate_final_texts(reviewed_queries: tuple[ReviewedQuery, ...]) -> None:
        seen: dict[str, str] = {}
        for item in reviewed_queries:
            if item.final_query_text is None:
                continue
            normalized = " ".join(item.final_query_text.casefold().split())
            if normalized in seen:
                raise DuplicateFinalQueryError(
                    "duplicate final query text for Draft queries "
                    f"{seen[normalized]} and {item.original_query.query_id}"
                )
            seen[normalized] = item.original_query.query_id

    @staticmethod
    def _stable_id(prefix: str, value: object) -> str:
        signature = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = sha256(signature.encode("utf-8")).hexdigest()[:12]
        return f"{prefix}_{digest}"
