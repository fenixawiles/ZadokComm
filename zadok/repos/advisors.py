from __future__ import annotations

import sqlite3

from ..utils import now_iso


def insert(db: sqlite3.Connection, *, slug: str, display_name: str, sign_off_name: str, email: str,
           role: str = "advisor", voice_key: str) -> int:
    cur = db.execute(
        "INSERT INTO advisors (slug, display_name, sign_off_name, email, role, voice_key, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (slug, display_name, sign_off_name, email, role, voice_key, now_iso()),
    )
    return cur.lastrowid


def all_active(db: sqlite3.Connection) -> list[sqlite3.Row]:
    return db.execute("SELECT * FROM advisors WHERE active = 1 ORDER BY role, display_name").fetchall()


def by_slug(db: sqlite3.Connection, slug: str) -> sqlite3.Row | None:
    return db.execute("SELECT * FROM advisors WHERE slug = ?", (slug,)).fetchone()


def by_id(db: sqlite3.Connection, advisor_id: int) -> sqlite3.Row | None:
    return db.execute("SELECT * FROM advisors WHERE id = ?", (advisor_id,)).fetchone()


def new_client_team(db: sqlite3.Connection) -> sqlite3.Row | None:
    return db.execute("SELECT * FROM advisors WHERE role = 'new_client_team' AND active = 1 LIMIT 1").fetchone()
