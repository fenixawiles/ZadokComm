from __future__ import annotations

import sqlite3

from ..utils import now_iso


def insert(db: sqlite3.Connection, *, thread_id: int, message_id: int, draft_id: int | None, field_hint: str,
           requested_change: str, quote: str, source: str) -> int:
    cur = db.execute(
        "INSERT INTO profile_change_requests (thread_id, message_id, draft_id, field_hint, requested_change,"
        " quote, source, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (thread_id, message_id, draft_id, field_hint, requested_change, quote, source, now_iso()),
    )
    return cur.lastrowid


def by_id(db: sqlite3.Connection, change_id: int) -> sqlite3.Row | None:
    return db.execute("SELECT * FROM profile_change_requests WHERE id = ?", (change_id,)).fetchone()


def for_message(db: sqlite3.Connection, message_id: int) -> list[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM profile_change_requests WHERE message_id = ? ORDER BY id", (message_id,)
    ).fetchall()


def open_for_thread(db: sqlite3.Connection, thread_id: int) -> list[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM profile_change_requests WHERE thread_id = ? AND status = 'open' ORDER BY id",
        (thread_id,),
    ).fetchall()


def resolve(db: sqlite3.Connection, change_id: int, *, status: str, advisor_id: int) -> None:
    db.execute(
        "UPDATE profile_change_requests SET status = ?, resolved_by_advisor_id = ?, resolved_at = ?"
        " WHERE id = ? AND status = 'open'",
        (status, advisor_id, now_iso(), change_id),
    )
