"""Credential-safe application boundary for the local Growth OS UI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from domain.campaign import (
    CampaignBrief,
    CampaignParseProvenance,
    CampaignParseResult,
)
from domain.icp import BusinessContext, ICPRunContext, ICPSelection
from domain.models import Review, utc_now_iso
from domain.query_review import QueryReviewAction
from pipeline.channels import CHANNELS, all_channel_status
from pipeline.os_runner import execute_approved_plan
from pipeline.icp_discovery import (
    DeterministicICPProvider,
    EnvironmentLLMICPProvider,
    ICPDiscoveryError,
    ICPDiscoveryService,
    confirm_discovery_criteria,
    generate_discovery_criteria,
    next_hypothesis_version,
)
from pipeline.partner_types import derive_partner_type, partner_type_counts
from pipeline.query_review import HumanQueryReviewer, QueryReviewError
from pipeline.search_plan_demo import run_search_plan_demo
from pipeline.search_plan import DeterministicSearchPlanProvider, SearchPlanGenerator
from storage.sqlite_store import SQLiteStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "creator_discovery_os_v1.db"

PRIORITY_ORDER: tuple[str, ...] = ("P1", "P2", "P3", "Needs Review")

# The built-in demo has no credential and can never fail to connect, so it is
# presented in the same card shape as the four real channels rather than as a
# second concept the reader has to learn.
CONTROLLED_CHANNEL_STATUS: dict[str, Any] = {
    "channel": "controlled",
    "label": "Controlled Demo",
    "purpose": "Offline fixture records, always available",
    "configured": True,
    "status": "connected",
    "environment_variables": [],
    "credential_variable": None,
}

# Product-facing key -> the stored CreatorSignals field it reads. The card names
# are shorter than the signal names because the detail view has no room for
# "content_relevance" next to a value.
KEY_SIGNAL_FIELDS: tuple[tuple[str, str], ...] = (
    ("activity", "activity"),
    ("relevance", "content_relevance"),
    ("audience", "audience_size"),
    ("market", "market"),
    ("actionability", "actionability"),
)

# A stored reason is one sentence with the decision in front and a qualifying
# clause behind one of these connectors. Cutting at the connector keeps the
# claim and drops the caveat; it never adds a word.
REASON_TAIL_CONNECTORS: tuple[str, ...] = ("; ", ", so ", ", which ", ", but ", ", and ", ", not ")

# Three clauses is what the priority card can show without becoming the wall of
# text the summary-first payload exists to replace.
PRIORITY_SUMMARY_REASON_LIMIT = 3

# Enough samples to prove the record is real; the rest sit behind "Show more".
CONTENT_SAMPLES_PREVIEW_LIMIT = 3


class UIServiceError(RuntimeError):
    """An expected UI workflow error safe to return to the local browser."""

    def __init__(self, message: str, *, code: str = "ui_workflow_error") -> None:
        super().__init__(message)
        self.code = code


class CreatorDiscoveryUIService:
    """Adapts frozen backend contracts without reimplementing business logic."""

    def __init__(self, database_path: str | Path = DEFAULT_DATABASE_PATH) -> None:
        self.database_path = Path(database_path)
        self._workflows: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def generate_search_plan(self, original_brief: str) -> dict[str, Any]:
        if not isinstance(original_brief, str) or not original_brief.strip():
            raise UIServiceError(
                "Describe the creator campaign before generating a search plan.",
                code="brief_required",
            )
        campaign_id = f"campaign_ui_{uuid4().hex[:12]}"
        brief = CampaignBrief(
            campaign_id=campaign_id,
            original_brief=original_brief,
        )
        campaign_result, draft_plan = run_search_plan_demo(brief=brief)
        workflow_id = f"workflow_{uuid4().hex[:12]}"
        with self._lock:
            self._workflows[workflow_id] = {
                "brief": brief,
                "campaign_result": campaign_result,
                "draft_plan": draft_plan,
            }
        return {
            "workflow_id": workflow_id,
            "original_brief": brief.original_brief,
            "campaign_parse": campaign_result.to_dict(),
            "draft_search_plan": draft_plan.to_dict() if draft_plan else None,
        }

    def generate_icp_hypotheses(
        self, payload: dict[str, Any], *, provider_mode: str = "mock"
    ) -> dict[str, Any]:
        """Persist human context and return exactly three testable hypotheses."""

        try:
            context = BusinessContext(
                context_id=f"context_{uuid4().hex[:12]}",
                product_name=payload.get("product_name"),
                website_url=payload.get("website_url"),
                product_description=payload.get("product_description"),
                problem=payload.get("problem"),
                strongest_value=payload.get("strongest_value"),
                current_users=payload.get("current_users"),
                current_alternatives=self._text_items(payload.get("current_alternatives", [])),
                pain_signals=self._text_items(payload.get("pain_signals", [])),
                target_markets=self._text_items(payload.get("target_markets", [])),
                stage=payload.get("stage"),
                created_at=utc_now_iso(),
            )
        except (TypeError, ValueError) as exc:
            raise UIServiceError(str(exc), code="insufficient_business_context") from exc

        if provider_mode == "mock":
            provider = DeterministicICPProvider()
        elif provider_mode == "live":
            try:
                provider = EnvironmentLLMICPProvider()
            except ICPDiscoveryError as exc:
                raise UIServiceError(str(exc), code=exc.error_code) from exc
        else:
            raise UIServiceError(
                "ICP provider mode must be mock or live.", code="invalid_icp_provider"
            )

        with self._lock, SQLiteStore(self.database_path) as store:
            store.add_product_event(
                event_name="icp_discovery_started",
                context_id=context.context_id,
                occurred_at=context.created_at,
                metadata={"provider_mode": provider_mode},
            )
            store.save_business_context(context)
            store.add_product_event(
                event_name="business_context_completed",
                context_id=context.context_id,
                occurred_at=utc_now_iso(),
                metadata={"has_website": bool(context.website_url)},
            )

        try:
            result = ICPDiscoveryService(provider).generate(context)
        except ICPDiscoveryError as exc:
            with self._lock, SQLiteStore(self.database_path) as store:
                store.add_product_event(
                    event_name="icp_generation_failed",
                    context_id=context.context_id,
                    occurred_at=utc_now_iso(),
                    metadata={"error_code": exc.error_code, "provider": provider.provider_name},
                )
            raise UIServiceError(str(exc), code=exc.error_code) from exc

        with self._lock, SQLiteStore(self.database_path) as store:
            for hypothesis in result.hypotheses:
                store.save_icp_hypothesis(hypothesis)
            store.add_product_event(
                event_name="icp_hypotheses_generated",
                context_id=context.context_id,
                occurred_at=result.provenance.generated_at,
                metadata={
                    "provider": result.provenance.provider,
                    "model": result.provenance.model,
                    "prompt_version": result.provenance.prompt_version,
                    "duration_ms": result.provenance.duration_ms,
                    "count": len(result.hypotheses),
                },
            )
        return result.to_dict()

    def edit_icp_hypothesis(
        self, *, hypothesis_id: str, version: int, changes: dict[str, Any]
    ) -> dict[str, Any]:
        if not isinstance(changes, dict) or not changes:
            raise UIServiceError("ICP edits are required.", code="invalid_icp_edit")
        try:
            with self._lock, SQLiteStore(self.database_path) as store:
                hypothesis = store.get_icp_hypothesis(hypothesis_id, int(version))
                if hypothesis is None:
                    raise UIServiceError("ICP hypothesis not found.", code="icp_not_found")
                edited = next_hypothesis_version(hypothesis, changes)
                store.save_icp_hypothesis(edited)
                store.add_product_event(
                    event_name="icp_hypothesis_edited",
                    context_id=edited.business_context_id,
                    hypothesis_id=edited.hypothesis_id,
                    hypothesis_version=edited.version,
                    occurred_at=edited.created_at,
                    metadata={"source_version": hypothesis.version, "changed_fields": sorted(changes)},
                )
            return edited.to_dict()
        except UIServiceError:
            raise
        except (TypeError, ValueError) as exc:
            raise UIServiceError(str(exc), code="invalid_icp_edit") from exc

    def select_icp_hypothesis(
        self, *, hypothesis_id: str, version: int
    ) -> dict[str, Any]:
        with self._lock, SQLiteStore(self.database_path) as store:
            hypothesis = store.get_icp_hypothesis(hypothesis_id, int(version))
            if hypothesis is None:
                raise UIServiceError("ICP hypothesis not found.", code="icp_not_found")
            context = store.get_business_context(hypothesis.business_context_id)
            if context is None:
                raise UIServiceError("Business Context not found.", code="business_context_not_found")
            selection = ICPSelection(
                selection_id=f"selection_{uuid4().hex[:12]}",
                hypothesis_id=hypothesis.hypothesis_id,
                hypothesis_version=hypothesis.version,
                status="TESTING",
                selected_at=utc_now_iso(),
            )
            criteria = generate_discovery_criteria(hypothesis, context)
            store.save_icp_selection(selection)
            store.save_discovery_criteria(criteria)
            store.add_product_event(
                event_name="icp_hypothesis_selected",
                context_id=context.context_id,
                hypothesis_id=hypothesis.hypothesis_id,
                hypothesis_version=hypothesis.version,
                occurred_at=selection.selected_at,
                metadata={"selection_id": selection.selection_id},
            )
            store.add_product_event(
                event_name="discovery_criteria_generated",
                context_id=context.context_id,
                hypothesis_id=hypothesis.hypothesis_id,
                hypothesis_version=hypothesis.version,
                criteria_id=criteria.criteria_id,
                occurred_at=criteria.created_at,
                metadata={"criteria_version": criteria.criteria_version, "status": criteria.status},
            )
        return {"selection": selection.to_dict(), "criteria": criteria.to_dict()}

    def confirm_icp_criteria(
        self, *, criteria_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        with self._lock, SQLiteStore(self.database_path) as store:
            draft = store.get_discovery_criteria(criteria_id)
            if draft is None:
                raise UIServiceError("Discovery Criteria not found.", code="criteria_not_found")
            try:
                confirmed = confirm_discovery_criteria(
                    draft,
                    partner_profile=payload.get("partner_profile", draft.partner_profile),
                    goal=payload.get("goal", draft.goal),
                    target_markets=self._text_items(payload.get("target_markets", draft.target_markets)),
                    content_themes=self._text_items(payload.get("content_themes", draft.content_themes)),
                    target_audience=self._text_items(payload.get("target_audience", draft.target_audience)),
                    intent_signals=self._text_items(payload.get("intent_signals", draft.intent_signals)),
                    exclusions=self._text_items(payload.get("exclusions", draft.exclusions)),
                    channels=self._text_items(payload.get("channels", draft.channels)),
                )
            except ICPDiscoveryError as exc:
                raise UIServiceError(str(exc), code=exc.error_code) from exc
            store.save_discovery_criteria(confirmed)
            hypothesis = store.get_icp_hypothesis(
                confirmed.hypothesis_id, confirmed.hypothesis_version
            )
            if hypothesis is None:
                raise UIServiceError("ICP hypothesis not found.", code="icp_not_found")
            selection_row = store.connection.execute(
                """SELECT * FROM icp_selections
                   WHERE hypothesis_id = ? AND hypothesis_version = ?
                   ORDER BY selected_at DESC LIMIT 1""",
                (confirmed.hypothesis_id, confirmed.hypothesis_version),
            ).fetchone()
            if selection_row is None:
                raise UIServiceError("ICP selection not found.", code="icp_selection_not_found")
            store.add_product_event(
                event_name="discovery_criteria_confirmed",
                context_id=hypothesis.business_context_id,
                hypothesis_id=hypothesis.hypothesis_id,
                hypothesis_version=hypothesis.version,
                criteria_id=confirmed.criteria_id,
                occurred_at=confirmed.confirmed_at or utc_now_iso(),
                metadata={"source_criteria_id": draft.criteria_id},
            )

        campaign_id = f"campaign_icp_{uuid4().hex[:12]}"
        definition = confirmed.to_campaign_definition(campaign_id)
        original_context = self._context_original_text(hypothesis.business_context_id)
        brief = CampaignBrief(campaign_id=campaign_id, original_brief=original_context)
        campaign_result = CampaignParseResult(
            brief=brief,
            definition=definition,
            status="complete",
            missing_required_fields=(),
            clarification_questions=(),
            provenance=CampaignParseProvenance(
                provider="human_confirmed_icp",
                model=confirmed.criteria_version,
                prompt_version=confirmed.criteria_version,
                parsed_at=confirmed.confirmed_at or utc_now_iso(),
            ),
        )
        draft_plan = SearchPlanGenerator(DeterministicSearchPlanProvider()).generate(definition)
        workflow_id = f"workflow_{uuid4().hex[:12]}"
        run_context = ICPRunContext(
            hypothesis_id=hypothesis.hypothesis_id,
            hypothesis_version=hypothesis.version,
            hypothesis_name=hypothesis.name,
            hypothesis_created_at=hypothesis.created_at,
            selected_at=selection_row["selected_at"],
            criteria_id=confirmed.criteria_id,
            criteria_snapshot=confirmed.to_dict(),
        )
        with self._lock:
            self._workflows[workflow_id] = {
                "brief": brief,
                "campaign_result": campaign_result,
                "draft_plan": draft_plan,
                "icp_run_context": run_context,
            }
        return {
            "workflow_id": workflow_id,
            "original_brief": brief.original_brief,
            "campaign_parse": campaign_result.to_dict(),
            "draft_search_plan": draft_plan.to_dict(),
            "icp_context": run_context.to_dict(),
            "confirmed_criteria": confirmed.to_dict(),
        }

    def bootstrap(self) -> dict[str, Any]:
        """Return the current SQLite-backed UI state without secret values."""

        with self._lock, SQLiteStore(self.database_path) as store:
            runs = [dict(row) for row in reversed(store.get_run_history())]
            query_history = [
                dict(row) for row in reversed(store.get_query_execution_history())
            ]
            creators, raw_profiles = self._creator_rows(store)
            priority_counts = store.get_priority_counts()
            review_count = store.count("reviews")
            total_partners = store.count("creators")
            # A record with three reviews is still one reviewed partner.
            reviewed_partners = int(
                store.connection.execute(
                    "SELECT COUNT(DISTINCT record_id) FROM reviews"
                ).fetchone()[0]
            )
            icp_workspace = self._icp_workspace(store)
        latest_run = runs[0] if runs else None
        ordered_priority_counts = {
            priority: priority_counts.get(priority, 0) for priority in PRIORITY_ORDER
        }
        return {
            "workspace": {
                "database_name": self.database_path.name,
                "providers": {
                    "controlled": {"configured": True, "label": "Offline fixtures"},
                    "instagram": {
                        "configured": bool(os.getenv("APIFY_API_TOKEN", "").strip()),
                        "label": "Apify Instagram",
                    },
                    "x": {
                        "configured": bool(os.getenv("X_BEARER_TOKEN", "").strip()),
                        "label": "X API recent search",
                    },
                },
                "channels": [dict(CONTROLLED_CHANNEL_STATUS), *all_channel_status()],
            },
            "overview": {
                "total_creators": len(creators),
                "priority_counts": ordered_priority_counts,
                "review_count": review_count,
                "latest_run": latest_run,
            },
            "partner_pool": {
                "total": total_partners,
                "priority_counts": ordered_priority_counts,
                "reviewed": reviewed_partners,
                "unreviewed": total_partners - reviewed_partners,
                "channel_counts": self._channel_counts(raw_profiles),
                "partner_type_counts": partner_type_counts(raw_profiles),
            },
            "latest_discovery": self._latest_discovery(latest_run),
            "creators": creators,
            "runs": runs,
            "query_history": query_history,
            "icp_workspace": icp_workspace,
        }

    def run_discovery(
        self,
        *,
        workflow_id: str,
        actions: list[dict[str, Any]],
        mode: str,
        confirm_live: bool = False,
    ) -> dict[str, Any]:
        if mode not in {"controlled", "live"}:
            raise UIServiceError(
                "Discovery mode must be controlled or live.", code="invalid_mode"
            )
        if mode == "live" and confirm_live is not True:
            raise UIServiceError(
                "Live retrieval requires explicit confirmation.",
                code="live_confirmation_required",
            )
        if not isinstance(workflow_id, str):
            raise UIServiceError("Workflow ID is required.", code="workflow_required")
        if not isinstance(actions, list):
            raise UIServiceError(
                "Every Draft query needs a human decision.",
                code="review_actions_required",
            )

        with self._lock:
            workflow = self._workflows.get(workflow_id)
            if workflow is None:
                raise UIServiceError(
                    "This Draft Search Plan is no longer in the local server session. Generate it again.",
                    code="workflow_not_found",
                )
            draft_plan = workflow.get("draft_plan")
            if draft_plan is None:
                raise UIServiceError(
                    "An incomplete campaign cannot be reviewed or executed.",
                    code="draft_plan_missing",
                )
            try:
                review_actions = tuple(
                    QueryReviewAction(
                        query_id=item.get("query_id"),
                        decision=item.get("decision"),
                        edited_query_text=item.get("edited_query_text"),
                        human_comment=item.get("human_comment"),
                        reviewed_at=utc_now_iso(),
                    )
                    for item in actions
                )
                review, approved_plan = HumanQueryReviewer().review(
                    draft_plan,
                    review_actions,
                    completed_at=utc_now_iso(),
                )
            except (QueryReviewError, TypeError, ValueError) as exc:
                raise UIServiceError(str(exc), code="query_review_invalid") from exc

            summary = execute_approved_plan(
                approved_plan,
                mode=mode,
                database_path=self.database_path,
                seed_controlled_review=False,
                icp_run_context=workflow.get("icp_run_context"),
            )
            workflow["review"] = review
            workflow["approved_plan"] = approved_plan
            workflow["run_id"] = summary["run_id"]
            if workflow.get("icp_run_context") is not None:
                context = workflow["icp_run_context"]
                with SQLiteStore(self.database_path) as store:
                    hypothesis = store.get_icp_hypothesis(
                        context.hypothesis_id, context.hypothesis_version
                    )
                    store.add_product_event(
                        event_name="discovery_run_started_from_icp",
                        context_id=hypothesis.business_context_id if hypothesis else None,
                        hypothesis_id=context.hypothesis_id,
                        hypothesis_version=context.hypothesis_version,
                        criteria_id=context.criteria_id,
                        run_id=summary["run_id"],
                        occurred_at=utc_now_iso(),
                        metadata={"mode": mode},
                    )

        return {
            "review": review.to_dict(),
            "approved_search_plan": approved_plan.to_dict(),
            "run_summary": {
                key: summary[key]
                for key in (
                    "run_id",
                    "mode",
                    "run_status",
                    "run_error_code",
                    "retrieved",
                    "duplicates",
                    "new_creators",
                    "new_creator_yield",
                    "signals",
                    "audience_inferences",
                    "priority_counts",
                    "query_history",
                )
            },
        }

    def creator_detail(self, record_id: str) -> dict[str, Any]:
        with self._lock, SQLiteStore(self.database_path) as store:
            row = store.connection.execute(
                """SELECT c.*, s.signals_json, s.extracted_at,
                          a.inference_json, p.priority, p.reasons_json,
                          p.signal_evidence_json, p.decided_at
                   FROM creators c
                   LEFT JOIN creator_signals s USING(record_id)
                   LEFT JOIN audience_inferences a USING(record_id)
                   LEFT JOIN priority_decisions p USING(record_id)
                   WHERE c.record_id = ?""",
                (record_id,),
            ).fetchone()
            if row is None:
                raise UIServiceError("Creator record not found.", code="creator_not_found")
            review = store.connection.execute(
                """SELECT review_id, status, structured_reason, comment, reviewed_at
                   FROM reviews WHERE record_id = ? ORDER BY reviewed_at DESC, review_id DESC
                   LIMIT 1""",
                (record_id,),
            ).fetchone()
        raw = json.loads(row["raw_json"])
        signals = json.loads(row["signals_json"]) if row["signals_json"] else None
        inference = json.loads(row["inference_json"]) if row["inference_json"] else None
        evidence = json.loads(row["signal_evidence_json"] or "{}")
        reasons = json.loads(row["reasons_json"] or "[]")
        priority = row["priority"] or "Needs Review"
        samples = raw.get("content_samples") or []
        return {
            "record_id": record_id,
            "observed_facts": raw,
            "derived_signals": signals,
            "ai_audience_inference": inference,
            "priority_decision": {
                "priority": row["priority"],
                "reasons": reasons,
                "signal_evidence": evidence,
                "decided_at": row["decided_at"],
            },
            "human_decision": dict(review) if review else None,
            "partner_type": derive_partner_type(raw),
            "priority_summary": self._priority_summary(priority, reasons),
            # The signals table is the live record; the decision snapshot is the
            # fallback for a record prioritized before signals were re-extracted.
            "key_signals": self._key_signals(signals or evidence),
            "ai_audience_summary": self._audience_summary(inference),
            "content_samples_preview": min(CONTENT_SAMPLES_PREVIEW_LIMIT, len(samples)),
        }

    def submit_creator_review(
        self,
        *,
        record_id: str,
        status: str,
        structured_reason: str | None,
        comment: str | None,
    ) -> dict[str, Any]:
        if not isinstance(record_id, str) or not record_id.strip():
            raise UIServiceError("Creator record is required.", code="creator_required")
        if status not in {"approve", "reject", "needs_review"}:
            raise UIServiceError("Choose a valid review decision.", code="invalid_review")
        reason = self._optional_text(structured_reason)
        note = self._optional_text(comment)
        with self._lock, SQLiteStore(self.database_path) as store:
            exists = store.connection.execute(
                "SELECT 1 FROM creators WHERE record_id = ?", (record_id,)
            ).fetchone()
            if exists is None:
                raise UIServiceError("Creator record not found.", code="creator_not_found")
            reviewed_at = utc_now_iso()
            review_id = store.add_review(
                Review(
                    record_id=record_id,
                    status=status,
                    structured_reason=reason,
                    comment=note,
                    reviewed_at=reviewed_at,
                )
            )
        return {
            "review_id": review_id,
            "record_id": record_id,
            "status": status,
            "structured_reason": reason,
            "comment": note,
            "reviewed_at": reviewed_at,
        }

    @staticmethod
    def _channel_counts(raw_profiles: list[dict[str, Any]]) -> dict[str, int]:
        """Count stored records per channel, never asserting more than was stored.

        All four keys are always present so the UI can render a stable row, but a
        channel with no stored record stays at zero — a fabricated count here
        would read as evidence that a channel had run.
        """
        counts = {channel: 0 for channel in CHANNELS}
        for profile in raw_profiles:
            channel = profile.get("platform")
            if channel in counts:
                counts[channel] += 1
        return counts

    @staticmethod
    def _latest_discovery(latest_run: dict[str, Any] | None) -> dict[str, Any] | None:
        if latest_run is None:
            return None
        return {
            "retrieved": latest_run["retrieved"],
            "duplicates": latest_run["duplicates"],
            "new_partners": latest_run["new_creators"],
            "new_partner_yield": latest_run["new_creator_yield"],
            "mode": latest_run["discovery_mode"],
            "status": latest_run["status"],
            "completed_at": latest_run["completed_at"],
            "run_id": latest_run["run_id"],
        }

    @staticmethod
    def _priority_summary(priority: str, stored_reasons: list[Any]) -> dict[str, Any]:
        """Compress the stored priority reasons into card-sized clauses.

        Every clause is a literal prefix of a sentence prioritize.py already
        wrote. Reasons are only shortened, reordered and dropped here — inventing
        one would put a justification in front of a person that no stored
        decision supports.
        """
        ranked: list[tuple[bool, int, str]] = []
        for index, reason in enumerate(stored_reasons):
            if not isinstance(reason, str):
                continue
            clause = CreatorDiscoveryUIService._shorten_reason(reason)
            if not clause:
                continue
            # The decision rule is always stored first and always leads. Of the
            # trailing notes, one that records an absence carries the least, so
            # it is the first to fall off the end of the card.
            ranked.append((index > 0 and clause.startswith("No "), index, clause))
        ranked.sort(key=lambda item: (item[0], item[1]))
        clauses: list[str] = []
        for _, _, clause in ranked:
            if clause not in clauses:
                clauses.append(clause)
        return {
            "priority": priority,
            # Raw on purpose: the human label and its colour belong to the UI.
            "headline": priority,
            "reasons": clauses[:PRIORITY_SUMMARY_REASON_LIMIT],
        }

    @staticmethod
    def _shorten_reason(reason: str) -> str:
        clause = reason.strip()
        for connector in REASON_TAIL_CONNECTORS:
            head = clause.split(connector, 1)[0].strip()
            if head and head != clause:
                clause = head
        return clause.rstrip(".").strip()

    @staticmethod
    def _key_signals(signals: dict[str, Any]) -> list[dict[str, Any]]:
        cards = []
        for name, field in KEY_SIGNAL_FIELDS:
            signal = signals.get(field)
            if not isinstance(signal, dict):
                continue
            cards.append(
                {
                    "signal": name,
                    "value": signal.get("value", "unknown"),
                    "summary": signal.get("reason", ""),
                    "evidence": list(signal.get("evidence") or ()),
                }
            )
        return cards

    @staticmethod
    def _audience_summary(inference: dict[str, Any] | None) -> dict[str, Any] | None:
        if not inference:
            return None
        return {
            "likely_audience": inference.get("likely_audience", []),
            "confidence": inference.get("confidence", "unknown"),
            "evidence": inference.get("evidence", []),
            "provider": inference.get("provider"),
            "model": inference.get("model"),
        }

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise UIServiceError("Optional text fields must be text.", code="invalid_review")
        return value.strip() or None

    @staticmethod
    def _text_items(value: Any) -> tuple[str, ...]:
        if isinstance(value, str):
            value = value.split(",")
        if not isinstance(value, (list, tuple)):
            raise ValueError("List fields must be arrays or comma-separated text")
        return tuple(str(item).strip() for item in value if str(item).strip())

    def _context_original_text(self, context_id: str) -> str:
        with SQLiteStore(self.database_path) as store:
            context = store.get_business_context(context_id)
        if context is None:
            raise UIServiceError("Business Context not found.", code="business_context_not_found")
        # This is copied from a human-entered field; the confirmed criteria stay
        # separate and never overwrite it.
        return context.product_description or context.website_url or context.product_name

    @staticmethod
    def _icp_workspace(store: SQLiteStore) -> dict[str, Any]:
        hypotheses = store.get_latest_icp_hypotheses()
        selection = store.get_latest_icp_selection()
        current = None
        if selection is not None:
            hypothesis = store.get_icp_hypothesis(
                selection["hypothesis_id"], int(selection["hypothesis_version"])
            )
            criteria = (
                store.get_discovery_criteria(selection["criteria_id"])
                if selection["criteria_id"]
                else None
            )
            current = {
                "selection": {
                    "selection_id": selection["selection_id"],
                    "status": selection["status"],
                    "selected_at": selection["selected_at"],
                },
                "hypothesis": hypothesis.to_dict() if hypothesis else None,
                "criteria": criteria.to_dict() if criteria else None,
                "runs": [dict(row) for row in store.get_icp_runs(selection["hypothesis_id"])],
            }
        return {
            "current": current,
            "hypotheses": [hypothesis.to_dict() for hypothesis in hypotheses],
        }

    @staticmethod
    def _creator_rows(
        store: SQLiteStore,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Return the list rows plus the raw records they were built from.

        The pool counters need the stored raw JSON, and re-reading the table for
        them would let the two halves of one payload disagree.
        """
        rows = store.connection.execute(
            """SELECT c.record_id, c.raw_json, c.created_at,
                      s.signals_json, a.inference_json,
                      p.priority, p.reasons_json,
                      (SELECT r.status FROM reviews r WHERE r.record_id = c.record_id
                       ORDER BY r.reviewed_at DESC, r.review_id DESC LIMIT 1) AS review_status,
                      (SELECT r.reviewed_at FROM reviews r WHERE r.record_id = c.record_id
                       ORDER BY r.reviewed_at DESC, r.review_id DESC LIMIT 1) AS reviewed_at,
                      (SELECT r.structured_reason FROM reviews r WHERE r.record_id = c.record_id
                       ORDER BY r.reviewed_at DESC, r.review_id DESC LIMIT 1) AS review_reason,
                      (SELECT r.comment FROM reviews r WHERE r.record_id = c.record_id
                       ORDER BY r.reviewed_at DESC, r.review_id DESC LIMIT 1) AS review_comment
               FROM creators c
               LEFT JOIN creator_signals s USING(record_id)
               LEFT JOIN audience_inferences a USING(record_id)
               LEFT JOIN priority_decisions p USING(record_id)
               ORDER BY CASE p.priority
                          WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 ELSE 4 END,
                        c.created_at DESC"""
        ).fetchall()
        creators = []
        raw_profiles = []
        for row in rows:
            raw = json.loads(row["raw_json"])
            raw_profiles.append(raw)
            signals = json.loads(row["signals_json"]) if row["signals_json"] else {}
            inference = json.loads(row["inference_json"]) if row["inference_json"] else {}
            market_signal = signals.get("market", {})
            partner_type = derive_partner_type(raw)
            creators.append(
                {
                    "record_id": row["record_id"],
                    "display_name": raw.get("display_name") or CreatorDiscoveryUIService._handle(raw.get("profile_url")),
                    "handle": CreatorDiscoveryUIService._handle(raw.get("profile_url")),
                    "platform": raw.get("platform"),
                    # Same value under the product-facing name.
                    "channel": raw.get("platform"),
                    "partner_type": partner_type["partner_type"],
                    "partner_type_confidence": partner_type["confidence"],
                    "profile_url": raw.get("profile_url"),
                    "follower_count": raw.get("follower_count"),
                    "bio_text": raw.get("bio_text"),
                    "market": CreatorDiscoveryUIService._market_label(market_signal),
                    "market_fit": market_signal.get("value", "unknown"),
                    "activity": signals.get("activity", {}).get("value", "unknown"),
                    "relevance": signals.get("content_relevance", {}).get("value", "unknown"),
                    "likely_audience": inference.get("likely_audience", []),
                    "audience_confidence": inference.get("confidence", "unknown"),
                    "priority": row["priority"] or "Needs Review",
                    "priority_reasons": json.loads(row["reasons_json"] or "[]"),
                    "review_status": row["review_status"] or "unreviewed",
                    "reviewed_at": row["reviewed_at"],
                    "review_reason": row["review_reason"],
                    "review_comment": row["review_comment"],
                    "run_id": raw.get("run_id"),
                    "query_id": raw.get("query_id"),
                    "source_query_id": raw.get("source_query_id"),
                    "query_text": raw.get("query_text"),
                    "search_angle": raw.get("search_angle"),
                    "campaign_id": raw.get("campaign_id"),
                    "discovery_mode": raw.get("discovery_mode"),
                    "has_signals": bool(row["signals_json"]),
                    "has_audience_inference": bool(row["inference_json"]),
                    "has_priority_decision": bool(row["priority"]),
                    "created_at": row["created_at"],
                }
            )
        return creators, raw_profiles

    @staticmethod
    def _handle(profile_url: str | None) -> str:
        if not profile_url:
            return "unknown"
        parts = [part for part in profile_url.split("?")[0].split("/") if part]
        return f"@{parts[-1]}" if parts else "unknown"

    @staticmethod
    def _market_label(signal: dict[str, Any]) -> str | None:
        """Return the observed market term, or None when nothing was observed.

        Observed evidence is returned verbatim because it is a quotation. The
        "not observed" case is UI chrome, so it is left to the browser to
        phrase in the reader's language instead of being hard-coded here.
        """
        evidence = signal.get("evidence") or []
        if evidence:
            value = str(evidence[0]).removeprefix("Observed market term: ").rstrip(".")
            return value or None
        return None


# Compatibility aliases keep earlier integrations working while the public
# product surface becomes Growth OS.
PartnerDiscoveryUIService = CreatorDiscoveryUIService
GrowthOSUIService = CreatorDiscoveryUIService
