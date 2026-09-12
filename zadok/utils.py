"""Small shared helpers."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone


def now_dt() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return to_iso(now_dt())


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def loads(text: str | None, default=None):
    if not text:
        return default
    return json.loads(text)
