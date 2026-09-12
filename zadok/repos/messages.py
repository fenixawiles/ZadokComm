from __future__ import annotations

import sqlite3

from ..utils import now_iso


def insert(db: sqlite3.Connection, *, thread_id: int, direction: str, source: str, external_message_id: str,
           sender_display: str, body: str, occurred_at: str, triage: str | None = None,
           triage_reason: str | None = None) -> int:
    cur = db.execute(
        "INSERT INTO messages (thread_id, direction, source, external_message_id, sender_display, body,"
        " triage, triage_reason, occurred_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (thread_id, direction, source, external_message_id, sender_display, body,
         triage, triage_reason, occurred_at, now_iso()),
    )
    return cur.lastrowid


def by_id(db: sqlite3.Connection, message_id: int) -> sqlite3.Row | None:
    return db.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()


def by_external(db: sqlite3.Connection, source: str, external_message_id: str) -> sqlite3.Row | None:
    return db.execute(
        "SELECT * FROM messages WHERE source = ? AND external_message_id = ?",
        (source, external_message_id),
    ).fetchone()


def for_thread(db: sqlite3.Connection, thread_id: int) -> list[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM messages WHERE thread_id = ? ORDER BY occurred_at, id", (thread_id,)
    ).fetchall()


def latest_inbound(db: sqlite3.Connection, thread_id: int) -> sqlite3.Row | None:
    return db.execute(
        "SELECT * FROM messages WHERE thread_id = ? AND direction = 'inbound' ORDER BY occurred_at DESC, id DESC LIMIT 1",
        (thread_id,),
    ).fetchone()
