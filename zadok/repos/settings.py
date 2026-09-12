from __future__ import annotations

import sqlite3

from ..utils import now_iso


def get(db: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def put(db: sqlite3.Connection, key: str, value: str, advisor_id: int | None = None) -> None:
    db.execute(
        "INSERT INTO settings (key, value, updated_at, updated_by_advisor_id) VALUES (?, ?, ?, ?)"
        " ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at,"
        " updated_by_advisor_id = excluded.updated_by_advisor_id",
        (key, value, now_iso(), advisor_id),
    )
