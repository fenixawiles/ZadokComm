"""SQLite access: per-request connection, schema bootstrap, CLI-friendly connect."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import current_app, g

from .utils import now_iso

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _configure(conn: sqlite3.Connection) -> sqlite3.Connection:
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def connect(database_path: str) -> sqlite3.Connection:
    return _configure(sqlite3.connect(database_path))


@contextmanager
def open_db(database_path: str):
    conn = connect(database_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = connect(current_app.config["ZADOK"].database_path)
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(conn: sqlite3.Connection, assist_scope_default: str) -> None:
    """Create the schema and seed the runtime settings row."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO settings (key, value, updated_at) VALUES ('assist_scope', ?, ?) "
        "ON CONFLICT(key) DO NOTHING",
        (assist_scope_default, now_iso()),
    )
    conn.commit()
