from __future__ import annotations

import sqlite3

from ..utils import now_iso


def find_or_create(db: sqlite3.Connection, *, client_ref: str, channel: str, client_display_name: str,
                   subject: str | None, crm_source: str, assigned_advisor_id: int) -> sqlite3.Row:
    row = db.execute(
        "SELECT * FROM threads WHERE client_ref = ? AND channel = ?", (client_ref, channel)
    ).fetchone()
    if row is not None:
        return row
    now = now_iso()
    cur = db.execute(
        "INSERT INTO threads (client_ref, client_display_name, channel, subject, crm_source,"
        " assigned_advisor_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (client_ref, client_display_name, channel, subject, crm_source, assigned_advisor_id, now, now),
    )
    return by_id(db, cur.lastrowid)


def by_id(db: sqlite3.Connection, thread_id: int) -> sqlite3.Row | None:
    return db.execute("SELECT * FROM threads WHERE id = ?", (thread_id,)).fetchone()


def for_advisor(db: sqlite3.Connection, advisor_id: int) -> list[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM threads WHERE assigned_advisor_id = ? AND status = 'open'"
        " ORDER BY COALESCE(awaiting_reply_since, updated_at) ASC",
        (advisor_id,),
    ).fetchall()


def mark_inbound(db: sqlite3.Connection, thread_id: int, occurred_at: str) -> None:
    db.execute(
        "UPDATE threads SET awaiting_reply_since = COALESCE(awaiting_reply_since, ?),"
        " last_inbound_at = ?, updated_at = ? WHERE id = ?",
        (occurred_at, occurred_at, now_iso(), thread_id),
    )


def clear_awaiting(db: sqlite3.Connection, thread_id: int) -> None:
    db.execute(
        "UPDATE threads SET awaiting_reply_since = NULL, updated_at = ? WHERE id = ?",
        (now_iso(), thread_id),
    )
