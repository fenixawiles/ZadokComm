"""Fixture-backed stand-in for the future simple-salesforce connector."""
from __future__ import annotations

import json
from pathlib import Path

from .base import CrmConnector

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "salesforce_clients.json"


class MockSalesforceConnector(CrmConnector):
    source_name = "salesforce"

    def __init__(self, fixture_path: Path = FIXTURE_PATH):
        self._records = json.loads(Path(fixture_path).read_text(encoding="utf-8"))

    def lookup_client(self, email: str) -> dict | None:
        needle = (email or "").strip().lower()
        return next((dict(r) for r in self._records if r["email"].lower() == needle), None)

    def lookup_client_by_ref(self, ref_id: str) -> dict | None:
        return next((dict(r) for r in self._records if r["id"] == ref_id), None)
