"""Channel-agnostic inbound ingestion.

validate -> idempotency -> resolve client -> thread -> triage + detectors ->
draft decision (assist scope) -> audit at every step. Synchronous drafting is
a shell simplification; the call into drafting.service is queue-shaped so a
real deployment can move it behind a worker.
"""
from __future__ import annotations

import sqlite3

from .. import audit
from ..config import Config
from ..connectors import resolver
from ..domain.intents import PERSONAL, ROUTINE, classify, detect_profile_changes
from ..drafting import service as drafting_service
from ..repos import advisors as advisors_repo
from ..repos import messages as messages_repo
from ..repos import profile_changes as profile_repo
from ..repos import settings as settings_repo
from ..repos import threads as threads_repo
from ..utils import now_iso

REQUIRED_FIELDS = ("source", "external_message_id", "body")


class InvalidPayload(ValueError):
    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


def validate_payload(payload: dict) -> dict:
    problems = []
    if not isinstance(payload, dict):
        raise InvalidPayload(["payload must be a JSON object"])
    for field in REQUIRED_FIELDS:
        if not str(payload.get(field, "")).strip():
            problems.append(f"missing required field: {field}")
    sender = payload.get("from") or {}
    if not str(sender.get("email", "")).strip():
        problems.append("missing required field: from.email")
    if problems:
        raise InvalidPayload(problems)
    return {
        "source": str(payload["source"]).strip(),
        "external_message_id": str(payload["external_message_id"]).strip(),
        "channel": str(payload.get("channel", "email")).strip() or "email",
        "from_email": str(sender["email"]).strip(),
        "from_name": str(sender.get("name", "")).strip(),
        "subject": (str(payload["subject"]).strip() or None) if payload.get("subject") else None,
        "body": str(payload["body"]).strip(),
        "received_at": str(payload.get("received_at", "")).strip() or now_iso(),
    }


def ingest_message(db: sqlite3.Connection, cfg: Config, payload: dict) -> dict:
    clean = validate_payload(payload)

    existing = messages_repo.by_external(db, clean["source"], clean["external_message_id"])
    if existing is not None:
        audit.record(db, "inbound_duplicate_ignored", thread_id=existing["thread_id"],
                     message_id=existing["id"],
                     detail={"source": clean["source"], "external_message_id": clean["external_message_id"]})
        return {"thread_id": existing["thread_id"], "message_id": existing["id"],
                "draft_id": None, "duplicate": True}

    record, connector = resolver.resolve_client(resolver.build_connectors(cfg), clean["from_email"])
    if record is not None:
        advisor = advisors_repo.by_slug(db, record.get("advisor_slug", "")) or advisors_repo.new_client_team(db)
        ref = resolver.client_ref(connector, record)
        crm_source = connector.source_name
        display_name = record["display_name"]
    else:
        advisor = advisors_repo.new_client_team(db)
        if advisor is None:
            raise LookupError("No new_client_team advisor exists; run `flask seed` first")
        ref = f"unknown:{clean['from_email'].lower()}"
        crm_source = "unknown"
        display_name = clean["from_name"] or clean["from_email"]

    thread = threads_repo.find_or_create(
        db, client_ref=ref, channel=clean["channel"], client_display_name=display_name,
        subject=clean["subject"], crm_source=crm_source, assigned_advisor_id=advisor["id"],
    )

    classification = classify(clean["body"], client_known=record is not None)
    message_id = messages_repo.insert(
        db, thread_id=thread["id"], direction="inbound", source=clean["source"],
        external_message_id=clean["external_message_id"], sender_display=display_name,
        body=clean["body"], occurred_at=clean["received_at"],
        triage=classification.triage, triage_reason=classification.reason,
    )
    threads_repo.mark_inbound(db, thread["id"], clean["received_at"])

    audit.record(db, "inbound_received", thread_id=thread["id"], message_id=message_id,
                 detail={"source": clean["source"], "intent": classification.intent,
                         "triage": classification.triage, "triage_reason": classification.reason})
    if record is not None:
        audit.record(db, "client_resolved", thread_id=thread["id"], message_id=message_id,
                     detail={"crm_source": crm_source, "client_ref": ref})
    else:
        audit.record(db, "client_unmatched_routed_to_team", thread_id=thread["id"], message_id=message_id,
                     detail={"client_ref": ref})

    for finding in detect_profile_changes(clean["body"]):
        change_id = profile_repo.insert(
            db, thread_id=thread["id"], message_id=message_id, draft_id=None,
            field_hint=finding["field_hint"], requested_change=finding["requested_change"],
            quote=finding["quote"], source="detector",
        )
        audit.record(db, "profile_change_noted", thread_id=thread["id"], message_id=message_id,
                     detail={"change_id": change_id, "field_hint": finding["field_hint"],
                             "source": "detector"})

    draft_id = None
    assist_scope = settings_repo.get(db, "assist_scope", cfg.assist_scope_default)
    should_draft = classification.triage == ROUTINE or assist_scope == "all"
    if should_draft:
        message = messages_repo.by_id(db, message_id)
        draft = drafting_service.create_draft_for_message(db, cfg, thread=thread, message=message)
        draft_id = draft["id"]
    else:
        audit.record(db, "message_routed_personal", thread_id=thread["id"], message_id=message_id,
                     detail={"assist_scope": assist_scope, "reason": classification.reason})

    return {"thread_id": thread["id"], "message_id": message_id, "draft_id": draft_id,
            "duplicate": False, "triage": classification.triage, "intent": classification.intent}
