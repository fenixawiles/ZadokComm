from __future__ import annotations

import sqlite3

from ..utils import dumps, now_iso

ACTIVE_STATUSES = ("drafted", "needs_attention", "edited")


def insert(db: sqlite3.Connection, *, thread_id: int, in_reply_to_message_id: int, version: int, engine: str,
           model_id: str, model_registry_fingerprint: str, prompt_bundle: dict, intent: str, draft_text: str,
           claims: list, policy_flags: dict, guardrail_flags: list, context_packet: dict, outcome: str,
           status: str) -> int:
    now = now_iso()
    cur = db.execute(
        "INSERT INTO drafts (thread_id, in_reply_to_message_id, version, engine, model_id,"
        " model_registry_fingerprint, prompt_bundle_json, intent, draft_text, claims_json, policy_flags_json,"
        " guardrail_flags_json, context_packet_json, outcome, status, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (thread_id, in_reply_to_message_id, version, engine, model_id, model_registry_fingerprint,
         dumps(prompt_bundle), intent, draft_text, dumps(claims), dumps(policy_flags), dumps(guardrail_flags),
         dumps(context_packet), outcome, status, now, now),
    )
    return cur.lastrowid


def by_id(db: sqlite3.Connection, draft_id: int) -> sqlite3.Row | None:
    return db.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()


def active_for_message(db: sqlite3.Connection, message_id: int) -> sqlite3.Row | None:
    placeholders = ",".join("?" for _ in ACTIVE_STATUSES)
    return db.execute(
        f"SELECT * FROM drafts WHERE in_reply_to_message_id = ? AND status IN ({placeholders})"
        " ORDER BY version DESC LIMIT 1",
        (message_id, *ACTIVE_STATUSES),
    ).fetchone()


def latest_version(db: sqlite3.Connection, message_id: int) -> int:
    row = db.execute(
        "SELECT MAX(version) AS v FROM drafts WHERE in_reply_to_message_id = ?", (message_id,)
    ).fetchone()
    return row["v"] or 0


def approved_exists(db: sqlite3.Connection, message_id: int) -> bool:
    row = db.execute(
        "SELECT 1 FROM drafts WHERE in_reply_to_message_id = ? AND status = 'approved_sent' LIMIT 1",
        (message_id,),
    ).fetchone()
    return row is not None


def set_status(db: sqlite3.Connection, draft_id: int, status: str) -> None:
    db.execute("UPDATE drafts SET status = ?, updated_at = ? WHERE id = ?", (status, now_iso(), draft_id))


def set_edited(db: sqlite3.Connection, draft_id: int, edited_text: str, advisor_id: int) -> None:
    db.execute(
        "UPDATE drafts SET edited_text = ?, edited_by_advisor_id = ?, status = 'edited', updated_at = ?"
        " WHERE id = ?",
        (edited_text, advisor_id, now_iso(), draft_id),
    )


def final_text(row: sqlite3.Row) -> str:
    return row["edited_text"] if row["edited_text"] else row["draft_text"]
