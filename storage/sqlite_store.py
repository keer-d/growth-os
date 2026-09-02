"""SQLite system of record for the backend-only V1."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from domain.icp import (
    BusinessContext,
    DiscoveryCriteria,
    ICPEvaluation,
    ICPHypothesis,
    ICPRunContext,
    ICPSelection,
)
from domain.models import (
    AudienceInference,
    CreatorSignals,
    Feedback,
    PriorityDecision,
    QueryHistory,
    RawCreatorProfile,
    Review,
)
from domain.retrieval import QueryExecutionHistory


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    discovery_mode TEXT NOT NULL,
    campaign_id TEXT,
    approved_search_plan_id TEXT,
    status TEXT,
    error_code TEXT,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    retrieved INTEGER NOT NULL,
    duplicates INTEGER NOT NULL,
    new_creators INTEGER NOT NULL,
    new_creator_yield REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS query_executions (
    run_id TEXT NOT NULL,
    campaign_id TEXT NOT NULL,
    approved_search_plan_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    source_connector TEXT NOT NULL,
    query_text TEXT NOT NULL,
    search_angle TEXT NOT NULL,
    execution_status TEXT NOT NULL,
    retrieved INTEGER NOT NULL,
    duplicates INTEGER NOT NULL,
    new_creators INTEGER NOT NULL,
    new_creator_yield REAL,
    error_code TEXT,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    PRIMARY KEY (run_id, query_id),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS queries (
    run_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    source_connector TEXT NOT NULL,
    query_text TEXT NOT NULL,
    retrieved INTEGER NOT NULL,
    duplicates INTEGER NOT NULL,
    new_creators INTEGER NOT NULL,
    new_creator_yield REAL NOT NULL,
    PRIMARY KEY (run_id, query_id),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS creators (
    record_id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    profile_url TEXT NOT NULL,
    normalized_profile_url TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (platform, normalized_profile_url)
);

CREATE TABLE IF NOT EXISTS creator_signals (
    record_id TEXT PRIMARY KEY,
    signals_json TEXT NOT NULL,
    extracted_at TEXT NOT NULL,
    FOREIGN KEY (record_id) REFERENCES creators(record_id)
);

CREATE TABLE IF NOT EXISTS audience_inferences (
    record_id TEXT PRIMARY KEY,
    inference_json TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    inferred_at TEXT NOT NULL,
    FOREIGN KEY (record_id) REFERENCES creators(record_id)
);

CREATE TABLE IF NOT EXISTS priority_decisions (
    record_id TEXT PRIMARY KEY,
    priority TEXT NOT NULL,
    reasons_json TEXT NOT NULL,
    signal_evidence_json TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    FOREIGN KEY (record_id) REFERENCES creators(record_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT NOT NULL,
    status TEXT NOT NULL,
    structured_reason TEXT,
    comment TEXT,
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY (record_id) REFERENCES creators(record_id)
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT NOT NULL,
    review_id INTEGER,
    feedback_type TEXT NOT NULL,
    comment TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (record_id) REFERENCES creators(record_id),
    FOREIGN KEY (review_id) REFERENCES reviews(review_id)
);

CREATE TABLE IF NOT EXISTS business_contexts (
    context_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    website_url TEXT,
    product_description TEXT,
    problem TEXT NOT NULL,
    strongest_value TEXT NOT NULL,
    current_users TEXT NOT NULL,
    current_alternatives_json TEXT NOT NULL,
    pain_signals_json TEXT NOT NULL,
    target_markets_json TEXT NOT NULL,
    stage TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS icp_hypotheses (
    hypothesis_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    business_context_id TEXT NOT NULL,
    audience_type TEXT NOT NULL,
    name TEXT NOT NULL,
    who_text TEXT NOT NULL,
    context_text TEXT NOT NULL,
    core_pain TEXT NOT NULL,
    why_pain_matters TEXT NOT NULL,
    current_alternative TEXT NOT NULL,
    value_proposition TEXT NOT NULL,
    trigger_text TEXT NOT NULL,
    intent_signals_json TEXT NOT NULL,
    where_to_find_json TEXT NOT NULL,
    why_may_work TEXT NOT NULL,
    unknowns_json TEXT NOT NULL,
    evaluation_json TEXT NOT NULL,
    recommended_order INTEGER NOT NULL,
    test_priority_reason TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (hypothesis_id, version),
    FOREIGN KEY (business_context_id) REFERENCES business_contexts(context_id)
);

CREATE TABLE IF NOT EXISTS icp_selections (
    selection_id TEXT PRIMARY KEY,
    hypothesis_id TEXT NOT NULL,
    hypothesis_version INTEGER NOT NULL,
    status TEXT NOT NULL,
    selected_at TEXT NOT NULL,
    FOREIGN KEY (hypothesis_id, hypothesis_version)
        REFERENCES icp_hypotheses(hypothesis_id, version)
);

CREATE TABLE IF NOT EXISTS discovery_criteria (
    criteria_id TEXT PRIMARY KEY,
    source_criteria_id TEXT,
    hypothesis_id TEXT NOT NULL,
    hypothesis_version INTEGER NOT NULL,
    hypothesis_name TEXT NOT NULL,
    discovery_subject TEXT NOT NULL,
    partner_profile TEXT NOT NULL,
    goal TEXT NOT NULL,
    target_markets_json TEXT NOT NULL,
    content_themes_json TEXT NOT NULL,
    target_audience_json TEXT NOT NULL,
    intent_signals_json TEXT NOT NULL,
    exclusions_json TEXT NOT NULL,
    channels_json TEXT NOT NULL,
    status TEXT NOT NULL,
    criteria_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    confirmed_at TEXT,
    FOREIGN KEY (source_criteria_id) REFERENCES discovery_criteria(criteria_id),
    FOREIGN KEY (hypothesis_id, hypothesis_version)
        REFERENCES icp_hypotheses(hypothesis_id, version)
);

CREATE TABLE IF NOT EXISTS icp_run_links (
    run_id TEXT PRIMARY KEY,
    hypothesis_id TEXT NOT NULL,
    hypothesis_version INTEGER NOT NULL,
    hypothesis_name TEXT NOT NULL,
    hypothesis_created_at TEXT NOT NULL,
    selected_at TEXT NOT NULL,
    criteria_id TEXT NOT NULL,
    criteria_snapshot_json TEXT NOT NULL,
    linked_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id),
    FOREIGN KEY (criteria_id) REFERENCES discovery_criteria(criteria_id),
    FOREIGN KEY (hypothesis_id, hypothesis_version)
        REFERENCES icp_hypotheses(hypothesis_id, version)
);

CREATE TABLE IF NOT EXISTS product_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,
    context_id TEXT,
    hypothesis_id TEXT,
    hypothesis_version INTEGER,
    criteria_id TEXT,
    run_id TEXT,
    metadata_json TEXT NOT NULL,
    occurred_at TEXT NOT NULL
);
"""


class SQLiteStoreError(RuntimeError):
    """A SQLite operation failed without exposing stored record contents."""

    error_code = "sqlite_write_failure"

    def __init__(self, safe_message: str = "SQLite write failed"):
        super().__init__(safe_message)
        self.safe_message = safe_message


class SQLiteStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(self.path)
            self.connection.row_factory = sqlite3.Row
            self.connection.executescript(SCHEMA)
            self._migrate_runs_table()
        except (OSError, sqlite3.Error) as exc:
            raise SQLiteStoreError("SQLite initialization failed") from exc

    def __enter__(self) -> "SQLiteStore":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        try:
            if exc_type is None:
                self.connection.commit()
            else:
                self.connection.rollback()
        except sqlite3.Error as database_error:
            raise SQLiteStoreError("SQLite transaction finalization failed") from database_error
        finally:
            self.connection.close()

    def _migrate_runs_table(self) -> None:
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(runs)").fetchall()
        }
        additions = {
            "campaign_id": "TEXT",
            "approved_search_plan_id": "TEXT",
            "status": "TEXT",
            "error_code": "TEXT",
        }
        for name, sql_type in additions.items():
            if name not in columns:
                self.connection.execute(f"ALTER TABLE runs ADD COLUMN {name} {sql_type}")

    def _write(self, statement: str, parameters: tuple = ()) -> sqlite3.Cursor:
        try:
            return self.connection.execute(statement, parameters)
        except sqlite3.Error as exc:
            raise SQLiteStoreError() from exc

    def existing_creator_keys(self) -> dict[tuple[str, str], str]:
        rows = self.connection.execute(
            "SELECT record_id, platform, normalized_profile_url FROM creators"
        ).fetchall()
        return {(row["platform"], row["normalized_profile_url"]): row["record_id"] for row in rows}

    def save_run(
        self,
        *,
        run_id: str,
        discovery_mode: str,
        started_at: str,
        completed_at: str,
        retrieved: int,
        duplicates: int,
        new_creators: int,
        campaign_id: str | None = None,
        approved_search_plan_id: str | None = None,
        status: str = "COMPLETED",
        error_code: str | None = None,
    ) -> None:
        new_creator_yield = new_creators / retrieved if retrieved else 0.0
        self._write(
            """INSERT OR REPLACE INTO runs
               (run_id, discovery_mode, campaign_id, approved_search_plan_id,
                status, error_code, started_at, completed_at, retrieved, duplicates,
                new_creators, new_creator_yield)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                discovery_mode,
                campaign_id,
                approved_search_plan_id,
                status,
                error_code,
                started_at,
                completed_at,
                retrieved,
                duplicates,
                new_creators,
                new_creator_yield,
            ),
        )

    def save_query_history(self, history: QueryHistory) -> None:
        self._write(
            """INSERT OR REPLACE INTO queries
               (run_id, query_id, source_connector, query_text, retrieved, duplicates,
                new_creators, new_creator_yield)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                history.run_id,
                history.query_id,
                history.source_connector,
                history.query_text,
                history.retrieved,
                history.duplicates,
                history.new_creators,
                history.new_creator_yield,
            ),
        )

    def save_query_execution(self, history: QueryExecutionHistory) -> None:
        self._write(
            """INSERT OR REPLACE INTO query_executions
               (run_id, campaign_id, approved_search_plan_id, query_id, platform,
                source_connector, query_text, search_angle, execution_status,
                retrieved, duplicates, new_creators, new_creator_yield, error_code,
                started_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                history.run_id,
                history.campaign_id,
                history.approved_search_plan_id,
                history.query_id,
                history.platform,
                history.source_connector,
                history.query_text,
                history.search_angle,
                history.execution_status,
                history.retrieved,
                history.duplicates,
                history.new_creators,
                history.new_creator_yield,
                history.error_code,
                history.started_at,
                history.completed_at,
            ),
        )

    def save_creator(self, profile: RawCreatorProfile) -> None:
        self._write(
            """INSERT INTO creators
               (record_id, platform, profile_url, normalized_profile_url, raw_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                profile.record_id,
                profile.platform,
                profile.profile_url,
                profile.normalized_profile_url,
                json.dumps(profile.to_dict(), ensure_ascii=False),
                profile.retrieved_at,
            ),
        )

    def save_signals(self, signals: CreatorSignals) -> None:
        self._write(
            """INSERT OR REPLACE INTO creator_signals
               (record_id, signals_json, extracted_at) VALUES (?, ?, ?)""",
            (
                signals.record_id,
                json.dumps(signals.to_dict(), ensure_ascii=False),
                signals.extracted_at,
            ),
        )

    def save_audience_inference(self, inference: AudienceInference) -> None:
        self._write(
            """INSERT OR REPLACE INTO audience_inferences
               (record_id, inference_json, provider, model, prompt_version, inferred_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                inference.record_id,
                json.dumps(inference.to_dict(), ensure_ascii=False),
                inference.provider,
                inference.model,
                inference.prompt_version,
                inference.inferred_at,
            ),
        )

    def save_priority_decision(self, decision: PriorityDecision) -> None:
        self._write(
            """INSERT OR REPLACE INTO priority_decisions
               (record_id, priority, reasons_json, signal_evidence_json, decided_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                decision.record_id,
                decision.priority,
                json.dumps(decision.reasons, ensure_ascii=False),
                json.dumps(decision.signal_evidence, ensure_ascii=False),
                decision.decided_at,
            ),
        )

    def add_review(self, review: Review) -> int:
        cursor = self._write(
            """INSERT INTO reviews
               (record_id, status, structured_reason, comment, reviewed_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                review.record_id,
                review.status,
                review.structured_reason,
                review.comment,
                review.reviewed_at,
            ),
        )
        return int(cursor.lastrowid)

    def add_feedback(self, feedback: Feedback) -> int:
        cursor = self._write(
            """INSERT INTO feedback
               (record_id, review_id, feedback_type, comment, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                feedback.record_id,
                feedback.review_id,
                feedback.feedback_type,
                feedback.comment,
                feedback.created_at,
            ),
        )
        return int(cursor.lastrowid)

    def save_business_context(self, context: BusinessContext) -> None:
        self._write(
            """INSERT INTO business_contexts
               (context_id, product_name, website_url, product_description, problem,
                strongest_value, current_users, current_alternatives_json,
                pain_signals_json, target_markets_json, stage, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                context.context_id,
                context.product_name,
                context.website_url,
                context.product_description,
                context.problem,
                context.strongest_value,
                context.current_users,
                json.dumps(context.current_alternatives, ensure_ascii=False),
                json.dumps(context.pain_signals, ensure_ascii=False),
                json.dumps(context.target_markets, ensure_ascii=False),
                context.stage,
                context.created_at,
            ),
        )

    def save_icp_hypothesis(self, hypothesis: ICPHypothesis) -> None:
        """Insert one immutable version; duplicate versions are rejected."""

        self._write(
            """INSERT INTO icp_hypotheses
               (hypothesis_id, version, business_context_id, audience_type, name,
                who_text, context_text, core_pain, why_pain_matters,
                current_alternative, value_proposition, trigger_text,
                intent_signals_json, where_to_find_json, why_may_work,
                unknowns_json, evaluation_json, recommended_order,
                test_priority_reason, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                hypothesis.hypothesis_id,
                hypothesis.version,
                hypothesis.business_context_id,
                hypothesis.audience_type,
                hypothesis.name,
                hypothesis.who,
                hypothesis.context,
                hypothesis.core_pain,
                hypothesis.why_pain_matters,
                hypothesis.current_alternative,
                hypothesis.value_proposition,
                hypothesis.trigger,
                json.dumps(hypothesis.intent_signals, ensure_ascii=False),
                json.dumps(hypothesis.where_to_find, ensure_ascii=False),
                hypothesis.why_may_work,
                json.dumps(hypothesis.unknowns, ensure_ascii=False),
                json.dumps(hypothesis.evaluation.to_dict(), ensure_ascii=False),
                hypothesis.recommended_order,
                hypothesis.test_priority_reason,
                hypothesis.status,
                hypothesis.created_at,
            ),
        )

    def save_icp_selection(self, selection: ICPSelection) -> None:
        self._write(
            """INSERT INTO icp_selections
               (selection_id, hypothesis_id, hypothesis_version, status, selected_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                selection.selection_id,
                selection.hypothesis_id,
                selection.hypothesis_version,
                selection.status,
                selection.selected_at,
            ),
        )

    def save_discovery_criteria(self, criteria: DiscoveryCriteria) -> None:
        self._write(
            """INSERT INTO discovery_criteria
               (criteria_id, source_criteria_id, hypothesis_id, hypothesis_version,
                hypothesis_name, discovery_subject, partner_profile, goal,
                target_markets_json, content_themes_json, target_audience_json,
                intent_signals_json, exclusions_json, channels_json, status,
                criteria_version, created_at, confirmed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                criteria.criteria_id,
                criteria.source_criteria_id,
                criteria.hypothesis_id,
                criteria.hypothesis_version,
                criteria.hypothesis_name,
                criteria.discovery_subject,
                criteria.partner_profile,
                criteria.goal,
                json.dumps(criteria.target_markets, ensure_ascii=False),
                json.dumps(criteria.content_themes, ensure_ascii=False),
                json.dumps(criteria.target_audience, ensure_ascii=False),
                json.dumps(criteria.intent_signals, ensure_ascii=False),
                json.dumps(criteria.exclusions, ensure_ascii=False),
                json.dumps(criteria.channels, ensure_ascii=False),
                criteria.status,
                criteria.criteria_version,
                criteria.created_at,
                criteria.confirmed_at,
            ),
        )

    def save_icp_run_link(
        self, *, run_id: str, context: ICPRunContext, linked_at: str
    ) -> None:
        self._write(
            """INSERT INTO icp_run_links
               (run_id, hypothesis_id, hypothesis_version, hypothesis_name,
                hypothesis_created_at, selected_at, criteria_id,
                criteria_snapshot_json, linked_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                context.hypothesis_id,
                context.hypothesis_version,
                context.hypothesis_name,
                context.hypothesis_created_at,
                context.selected_at,
                context.criteria_id,
                json.dumps(context.criteria_snapshot, ensure_ascii=False),
                linked_at,
            ),
        )

    def add_product_event(
        self,
        *,
        event_name: str,
        occurred_at: str,
        context_id: str | None = None,
        hypothesis_id: str | None = None,
        hypothesis_version: int | None = None,
        criteria_id: str | None = None,
        run_id: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        cursor = self._write(
            """INSERT INTO product_events
               (event_name, context_id, hypothesis_id, hypothesis_version,
                criteria_id, run_id, metadata_json, occurred_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event_name,
                context_id,
                hypothesis_id,
                hypothesis_version,
                criteria_id,
                run_id,
                json.dumps(metadata or {}, ensure_ascii=False),
                occurred_at,
            ),
        )
        return int(cursor.lastrowid)

    def get_business_context(self, context_id: str) -> BusinessContext | None:
        row = self.connection.execute(
            "SELECT * FROM business_contexts WHERE context_id = ?", (context_id,)
        ).fetchone()
        return self._business_context_from_row(row) if row else None

    def get_icp_hypothesis(
        self, hypothesis_id: str, version: int
    ) -> ICPHypothesis | None:
        row = self.connection.execute(
            """SELECT * FROM icp_hypotheses
               WHERE hypothesis_id = ? AND version = ?""",
            (hypothesis_id, version),
        ).fetchone()
        return self._hypothesis_from_row(row) if row else None

    def get_latest_icp_hypotheses(self) -> list[ICPHypothesis]:
        rows = self.connection.execute(
            """SELECT h.* FROM icp_hypotheses h
               JOIN (
                 SELECT hypothesis_id, MAX(version) AS version
                 FROM icp_hypotheses GROUP BY hypothesis_id
               ) latest
               ON latest.hypothesis_id = h.hypothesis_id
               AND latest.version = h.version
               ORDER BY h.created_at DESC, h.recommended_order"""
        ).fetchall()
        return [self._hypothesis_from_row(row) for row in rows]

    def get_discovery_criteria(self, criteria_id: str) -> DiscoveryCriteria | None:
        row = self.connection.execute(
            "SELECT * FROM discovery_criteria WHERE criteria_id = ?", (criteria_id,)
        ).fetchone()
        return self._criteria_from_row(row) if row else None

    def get_latest_icp_selection(self) -> sqlite3.Row | None:
        return self.connection.execute(
            """SELECT s.*, h.name, h.who_text, h.core_pain, h.value_proposition,
                      h.intent_signals_json, h.where_to_find_json, h.unknowns_json,
                      h.business_context_id, h.created_at AS hypothesis_created_at,
                      c.criteria_id, c.status AS criteria_status
               FROM icp_selections s
               JOIN icp_hypotheses h
                 ON h.hypothesis_id = s.hypothesis_id
                AND h.version = s.hypothesis_version
               LEFT JOIN discovery_criteria c
                 ON c.hypothesis_id = s.hypothesis_id
                AND c.hypothesis_version = s.hypothesis_version
               ORDER BY s.selected_at DESC, c.created_at DESC LIMIT 1"""
        ).fetchone()

    def get_icp_runs(self, hypothesis_id: str | None = None) -> list[sqlite3.Row]:
        where = "WHERE l.hypothesis_id = ?" if hypothesis_id else ""
        parameters = (hypothesis_id,) if hypothesis_id else ()
        return self.connection.execute(
            f"""SELECT l.*, r.discovery_mode, r.status, r.retrieved, r.duplicates,
                       r.new_creators, r.new_creator_yield, r.completed_at
                FROM icp_run_links l JOIN runs r USING(run_id)
                {where} ORDER BY r.started_at DESC""",
            parameters,
        ).fetchall()

    def get_product_events(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT * FROM product_events ORDER BY event_id"
        ).fetchall()

    def count(self, table: str) -> int:
        allowed = {
            "runs",
            "queries",
            "query_executions",
            "creators",
            "creator_signals",
            "audience_inferences",
            "priority_decisions",
            "reviews",
            "feedback",
            "business_contexts",
            "icp_hypotheses",
            "icp_selections",
            "discovery_criteria",
            "icp_run_links",
            "product_events",
        }
        if table not in allowed:
            raise ValueError("unsupported table")
        return int(self.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    def get_priority_counts(self) -> dict[str, int]:
        rows = self.connection.execute(
            "SELECT priority, COUNT(*) AS count FROM priority_decisions GROUP BY priority"
        ).fetchall()
        return {row["priority"]: int(row["count"]) for row in rows}

    def get_review(self, review_id: int) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM reviews WHERE review_id = ?", (review_id,)
        ).fetchone()

    def get_feedback(self, feedback_id: int) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM feedback WHERE feedback_id = ?", (feedback_id,)
        ).fetchone()

    def get_run_history(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            """SELECT run_id, campaign_id, approved_search_plan_id, discovery_mode,
                      status, error_code, started_at, completed_at, retrieved,
                      duplicates, new_creators, new_creator_yield
               FROM runs ORDER BY started_at, rowid"""
        ).fetchall()

    def get_query_execution_history(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            """SELECT run_id, campaign_id, approved_search_plan_id, query_id, platform,
                      source_connector, query_text, search_angle, execution_status,
                      retrieved, duplicates, new_creators, new_creator_yield,
                      error_code, started_at, completed_at
               FROM query_executions ORDER BY started_at, rowid"""
        ).fetchall()

    def get_saturation_evidence(self) -> list[sqlite3.Row]:
        """Return real per-run query yield evidence without optimizing queries."""

        return self.connection.execute(
            """SELECT query_id, query_text, search_angle, platform, run_id,
                      execution_status, retrieved, duplicates, new_creators,
                      new_creator_yield
               FROM query_executions
               ORDER BY query_id, started_at, rowid"""
        ).fetchall()

    @staticmethod
    def _business_context_from_row(row: sqlite3.Row) -> BusinessContext:
        return BusinessContext(
            context_id=row["context_id"],
            product_name=row["product_name"],
            website_url=row["website_url"],
            product_description=row["product_description"],
            problem=row["problem"],
            strongest_value=row["strongest_value"],
            current_users=row["current_users"],
            current_alternatives=tuple(json.loads(row["current_alternatives_json"])),
            pain_signals=tuple(json.loads(row["pain_signals_json"])),
            target_markets=tuple(json.loads(row["target_markets_json"])),
            stage=row["stage"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _hypothesis_from_row(row: sqlite3.Row) -> ICPHypothesis:
        evaluation = json.loads(row["evaluation_json"])
        evaluation.pop("comparison_score", None)
        return ICPHypothesis(
            hypothesis_id=row["hypothesis_id"],
            version=int(row["version"]),
            business_context_id=row["business_context_id"],
            audience_type=row["audience_type"],
            name=row["name"],
            who=row["who_text"],
            context=row["context_text"],
            core_pain=row["core_pain"],
            why_pain_matters=row["why_pain_matters"],
            current_alternative=row["current_alternative"],
            value_proposition=row["value_proposition"],
            trigger=row["trigger_text"],
            intent_signals=tuple(json.loads(row["intent_signals_json"])),
            where_to_find=tuple(json.loads(row["where_to_find_json"])),
            why_may_work=row["why_may_work"],
            unknowns=tuple(json.loads(row["unknowns_json"])),
            evaluation=ICPEvaluation(**evaluation),
            recommended_order=int(row["recommended_order"]),
            test_priority_reason=row["test_priority_reason"],
            status=row["status"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _criteria_from_row(row: sqlite3.Row) -> DiscoveryCriteria:
        return DiscoveryCriteria(
            criteria_id=row["criteria_id"],
            source_criteria_id=row["source_criteria_id"],
            hypothesis_id=row["hypothesis_id"],
            hypothesis_version=int(row["hypothesis_version"]),
            hypothesis_name=row["hypothesis_name"],
            discovery_subject=row["discovery_subject"],
            partner_profile=row["partner_profile"],
            goal=row["goal"],
            target_markets=tuple(json.loads(row["target_markets_json"])),
            content_themes=tuple(json.loads(row["content_themes_json"])),
            target_audience=tuple(json.loads(row["target_audience_json"])),
            intent_signals=tuple(json.loads(row["intent_signals_json"])),
            exclusions=tuple(json.loads(row["exclusions_json"])),
            channels=tuple(json.loads(row["channels_json"])),
            status=row["status"],
            criteria_version=row["criteria_version"],
            created_at=row["created_at"],
            confirmed_at=row["confirmed_at"],
        )
