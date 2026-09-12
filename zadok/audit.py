"""Append-only audit writer. Insert and read only — no update, no delete."""
from __future__ import annotations

import sqlite3

from .utils import dumps, now_iso

# The complete event vocabulary. Keeping it explicit makes the audit trail
# greppable and keeps typos from inventing new event kinds silently.
EVENTS = frozenset({
    "inbound_received",
    "inbound_duplicate_ignored",
    "client_resolved",
    "client_unmatched_routed_to_team",
    "message_routed_personal",
    "draft_created",
    "draft_flagged",
    "draft_failed",
    "draft_requested_manually",
    "draft_edited",
    "draft_regenerated",
    "draft_discarded",
    "flags_acknowledged",
    "draft_approved",
    "send_recorded",
    "profile_change_noted",
    "profile_change_acknowledged",
    "profile_change_dismissed",
    "assist_scope_changed",
    "advisor_login",
})


def record(
    db: sqlite3.Connection,
    event: str,
    *,
    actor_type: str = "system",
    actor_id: int | None = None,
    thread_id: int | None = None,
    message_id: int | None = None,
    draft_id: int | None = None,
    detail: dict | None = None,
) -> None:
    if event not in EVENTS:
        raise ValueError(f"Unknown audit event: {event!r}")
    db.execute(
        "INSERT INTO audit_log (occurred_at, actor_type, actor_id, event, thread_id, message_id, draft_id, detail_json)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (now_iso(), actor_type, actor_id, event, thread_id, message_id, draft_id, dumps(detail) if detail else None),
    )


def for_thread(db: sqlite3.Connection, thread_id: int) -> list[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM audit_log WHERE thread_id = ? ORDER BY occurred_at, id", (thread_id,)
    ).fetchall()
