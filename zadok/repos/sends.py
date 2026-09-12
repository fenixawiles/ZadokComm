from __future__ import annotations

import sqlite3

from ..utils import dumps, now_iso


def insert(db: sqlite3.Connection, *, draft_id: int, thread_id: int, outbound_message_id: int, sent_text: str,
           was_edited: bool, final_scan_flags: list, flags_acknowledged: bool, sender_impl: str,
           external_send_ref: str, sent_by_advisor_id: int) -> int:
    cur = db.execute(
        "INSERT INTO sends (draft_id, thread_id, outbound_message_id, sent_text, was_edited,"
        " final_scan_flags_json, flags_acknowledged, sender_impl, external_send_ref, sent_by_advisor_id, sent_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (draft_id, thread_id, outbound_message_id, sent_text, int(was_edited), dumps(final_scan_flags),
         int(flags_acknowledged), sender_impl, external_send_ref, sent_by_advisor_id, now_iso()),
    )
    return cur.lastrowid


def by_draft(db: sqlite3.Connection, draft_id: int) -> sqlite3.Row | None:
    return db.execute("SELECT * FROM sends WHERE draft_id = ?", (draft_id,)).fetchone()
