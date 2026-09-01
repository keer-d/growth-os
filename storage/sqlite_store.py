"""SQLite system of record for the backend-only V1."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from domain.models import (
    AudienceInference,
    CreatorSignals,
    Feedback,
    PriorityDecision,
    QueryHistory,
    RawCreatorProfile,
    Review,
)


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    discovery_mode TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    retrieved INTEGER NOT NULL,
    duplicates INTEGER NOT NULL,
    new_creators INTEGER NOT NULL,
    new_creator_yield REAL NOT NULL
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
"""


class SQLiteStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    def __enter__(self) -> "SQLiteStore":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()

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
    ) -> None:
        new_creator_yield = new_creators / retrieved if retrieved else 0.0
        self.connection.execute(
            """INSERT OR REPLACE INTO runs
               (run_id, discovery_mode, started_at, completed_at, retrieved, duplicates,
                new_creators, new_creator_yield)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                discovery_mode,
                started_at,
                completed_at,
                retrieved,
                duplicates,
                new_creators,
                new_creator_yield,
            ),
        )

    def save_query_history(self, history: QueryHistory) -> None:
        self.connection.execute(
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

    def save_creator(self, profile: RawCreatorProfile) -> None:
        self.connection.execute(
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
        self.connection.execute(
            """INSERT OR REPLACE INTO creator_signals
               (record_id, signals_json, extracted_at) VALUES (?, ?, ?)""",
            (
                signals.record_id,
                json.dumps(signals.to_dict(), ensure_ascii=False),
                signals.extracted_at,
            ),
        )

    def save_audience_inference(self, inference: AudienceInference) -> None:
        self.connection.execute(
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
        self.connection.execute(
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
        cursor = self.connection.execute(
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
        cursor = self.connection.execute(
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

    def count(self, table: str) -> int:
        allowed = {
            "runs",
            "queries",
            "creators",
            "creator_signals",
            "audience_inferences",
            "priority_decisions",
            "reviews",
            "feedback",
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
