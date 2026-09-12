"""`flask seed` — full synthetic demo state.

Advisors and historical thread context are inserted directly; every inbound
scenario then flows through the REAL ingestion pipeline, so the first login
shows an inbox the actual system produced (triage, drafts, detector cards,
audit trail), not staged rows. Alex's check-in is injected 30 hours old so
the SLA badge has something to show. Idempotent: rerunning skips existing
advisors and duplicate scenario messages.
"""
from __future__ import annotations

import sqlite3
from datetime import timedelta

from zadok.config import Config
from zadok.inbound.ingest import ingest_message
from zadok.inbound.scenarios import build_payload
from zadok.repos import advisors as advisors_repo
from zadok.repos import messages as messages_repo
from zadok.repos import threads as threads_repo
from zadok.utils import now_dt, to_iso

ADVISORS = [
    dict(slug="sarah-kline", display_name="Sarah Kline", sign_off_name="Sarah",
         email="sarah.kline@zadok.example", role="advisor", voice_key="sarah-kline"),
    dict(slug="elena-ruiz", display_name="Elena Ruiz", sign_off_name="Elena",
         email="elena.ruiz@zadok.example", role="advisor", voice_key="elena-ruiz"),
    dict(slug="michael-trent", display_name="Michael Trent", sign_off_name="Michael",
         email="michael.trent@zadok.example", role="advisor", voice_key="michael-trent"),
    dict(slug="new-client-team", display_name="New-Client Team", sign_off_name="Maya",
         email="welcome@zadok.example", role="new_client_team", voice_key="new-client-team"),
]

# (client_ref, display, crm_source, advisor_slug, sign_off, days_ago, historical outbound text)
HISTORY = [
    ("sf:C-1001", "Alex Morgan", "salesforce", "sarah-kline", "Sarah", 24,
     "It was great seeing you, Alex. I've made a note that the GMT-Master II remains your first choice, "
     "and I'll keep our conversation in mind."),
    ("woven:W-2002", "Mia Chen", "woven", "elena-ruiz", "Elena", 98,
     "I hope you're still enjoying the anniversary piece. It was a pleasure helping you select it."),
    ("sf:C-1002", "Daniel Ruiz", "salesforce", "michael-trent", "Michael", 21,
     "I appreciate you checking in, Daniel. I'll reach out directly if I have a meaningful update for you."),
]

# (scenario, hours_ago) — Alex lands past the default 24h SLA on purpose.
SCENARIOS = [
    ("alex_status_checkin", 30),
    ("mia_appointment_with_profile_change", 2),
    ("daniel_complaint", 20),
    ("jordan_new_prospect", 1),
    ("casey_pleasantry", 3),
]


def seed_advisors(db: sqlite3.Connection) -> int:
    created = 0
    for advisor in ADVISORS:
        if advisors_repo.by_slug(db, advisor["slug"]) is None:
            advisors_repo.insert(db, **advisor)
            created += 1
    return created


def seed_history(db: sqlite3.Connection) -> int:
    created = 0
    for ref, display, source, advisor_slug, sign_off, days_ago, text in HISTORY:
        advisor = advisors_repo.by_slug(db, advisor_slug)
        thread = threads_repo.find_or_create(
            db, client_ref=ref, channel="email", client_display_name=display,
            subject=None, crm_source=source, assigned_advisor_id=advisor["id"],
        )
        external_id = f"seed-history-{ref}"
        if messages_repo.by_external(db, "seed", external_id) is None:
            messages_repo.insert(
                db, thread_id=thread["id"], direction="outbound", source="seed",
                external_message_id=external_id, sender_display=sign_off, body=text,
                occurred_at=to_iso(now_dt() - timedelta(days=days_ago)),
            )
            created += 1
    return created


def seed_scenarios(db: sqlite3.Connection, cfg: Config) -> tuple[int, int]:
    injected = drafted = 0
    for name, hours_ago in SCENARIOS:
        payload = build_payload(
            name, external_id=f"seed-{name}",
            received_at=to_iso(now_dt() - timedelta(hours=hours_ago)), source="seed",
        )
        result = ingest_message(db, cfg, payload)
        if not result["duplicate"]:
            injected += 1
            if result["draft_id"]:
                drafted += 1
    return injected, drafted


def seed_all(db: sqlite3.Connection, cfg: Config) -> str:
    advisors_created = seed_advisors(db)
    history_created = seed_history(db)
    injected, drafted = seed_scenarios(db, cfg)
    return (f"Seeded: {advisors_created} advisors, {history_created} historical messages, "
            f"{injected} inbound scenarios ({drafted} auto-drafted). "
            f"Log in with any advisor + the DEV_PASSCODE.")
