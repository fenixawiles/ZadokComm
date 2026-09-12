"""Drafting orchestration: packet -> engine -> guardrails -> persisted draft + audit.

Deliberately queue-shaped: `create_draft_for_message` takes ids and rows and
returns a draft row, so a real deployment can move it behind an async worker
without touching callers.
"""
from __future__ import annotations

import sqlite3

from .. import audit
from ..config import Config
from ..connectors import resolver
from ..domain import states
from ..domain.intents import classify
from ..model_registry import get_artifact, registry_fingerprint
from ..protocols.loader import load_pack, load_voice
from ..repos import advisors as advisors_repo
from ..repos import drafts as drafts_repo
from ..repos import messages as messages_repo
from ..repos import profile_changes as profile_repo
from .engine import OUTCOME_COMPLETED, DraftEngine, DraftRequest
from .guardrails import evaluate_draft
from .mock_engine import MockDraftEngine
from .prompt_builder import build_system_prompt


def resolve_engine(cfg: Config) -> DraftEngine:
    """Gate-first engine selection: the live engine requires DRAFT_ENGINE=openai
    AND the spend gate AND a key. Anything else — including a stray key with
    the gate off — resolves to the mock engine."""
    if cfg.draft_engine == "openai" and cfg.effective_openai_api_key:
        from .openai_engine import build_live_engine

        return build_live_engine(cfg, get_artifact("draft"))
    return MockDraftEngine()


def _thread_history(db: sqlite3.Connection, thread_id: int, exclude_message_id: int, limit: int = 6):
    rows = messages_repo.for_thread(db, thread_id)
    history = [
        (row["direction"], row["sender_display"], row["body"])
        for row in rows
        if row["id"] != exclude_message_id
    ]
    return history[-limit:]


def build_packet_for_message(db: sqlite3.Connection, cfg: Config, thread, message, advisor_row):
    classification = classify(message["body"], client_known=thread["crm_source"] != "unknown")
    history = _thread_history(db, thread["id"], message["id"])
    if thread["crm_source"] == "unknown":
        packet = resolver.build_unknown_packet(
            email=thread["client_ref"].partition(":")[2],
            display_name=thread["client_display_name"],
            team_advisor_row=advisor_row,
            intent=classification.intent,
            inbound_text=message["body"],
            thread_history=history,
        )
        return packet, classification
    connectors = resolver.build_connectors(cfg)
    record, _connector = resolver.resolve_by_ref(connectors, thread["client_ref"])
    if record is None:
        raise LookupError(f"No CRM record behind thread ref {thread['client_ref']!r}")
    packet = resolver.build_packet(
        record,
        advisor_row=advisor_row,
        intent=classification.intent,
        inbound_text=message["body"],
        thread_history=history,
    )
    return packet, classification


def create_draft_for_message(db: sqlite3.Connection, cfg: Config, *, thread, message,
                             actor_type: str = "system", actor_id: int | None = None,
                             manual: bool = False) -> sqlite3.Row:
    advisor_row = advisors_repo.by_id(db, thread["assigned_advisor_id"])
    packet, classification = build_packet_for_message(db, cfg, thread, message, advisor_row)

    version = drafts_repo.latest_version(db, message["id"]) + 1
    pack = load_pack(classification.intent)
    voice_text, voice_hash = load_voice(advisor_row["voice_key"])
    engine = resolve_engine(cfg)

    result = engine.draft(DraftRequest(
        packet=packet,
        protocol_pack=pack,
        voice_profile=voice_text,
        voice_hash=voice_hash,
        variant=version - 1,
    ))

    prompt_bundle = result.prompt_bundle or build_system_prompt(pack, voice_text, voice_hash)[1]

    if result.outcome != OUTCOME_COMPLETED:
        draft_id = drafts_repo.insert(
            db, thread_id=thread["id"], in_reply_to_message_id=message["id"], version=version,
            engine=result.engine_name, model_id=result.model_id,
            model_registry_fingerprint=registry_fingerprint(), prompt_bundle=prompt_bundle,
            intent=result.intent, draft_text="", claims=[], policy_flags={}, guardrail_flags=[],
            context_packet=packet.to_dict(), outcome=result.outcome, status=states.FAILED,
        )
        audit.record(db, "draft_failed", actor_type=actor_type, actor_id=actor_id,
                     thread_id=thread["id"], message_id=message["id"], draft_id=draft_id,
                     detail={"outcome": result.outcome, "detail": result.detail, "version": version})
        return drafts_repo.by_id(db, draft_id)

    flags = evaluate_draft(
        result.draft_text,
        claims=result.claims_used,
        policy_check=result.policy_check,
        packet=packet,
        sign_off=advisor_row["sign_off_name"],
    )
    status = states.NEEDS_ATTENTION if flags else states.DRAFTED
    draft_id = drafts_repo.insert(
        db, thread_id=thread["id"], in_reply_to_message_id=message["id"], version=version,
        engine=result.engine_name, model_id=result.model_id,
        model_registry_fingerprint=registry_fingerprint(), prompt_bundle=prompt_bundle,
        intent=result.intent, draft_text=result.draft_text, claims=result.claims_used,
        policy_flags=result.policy_check, guardrail_flags=[f.to_dict() for f in flags],
        context_packet=packet.to_dict(), outcome=result.outcome, status=status,
    )
    if manual:
        audit.record(db, "draft_requested_manually", actor_type=actor_type, actor_id=actor_id,
                     thread_id=thread["id"], message_id=message["id"], draft_id=draft_id)
    audit.record(db, "draft_created", actor_type=actor_type, actor_id=actor_id, thread_id=thread["id"],
                 message_id=message["id"], draft_id=draft_id,
                 detail={"version": version, "engine": result.engine_name, "intent": result.intent,
                         "status": status})
    if flags:
        audit.record(db, "draft_flagged", actor_type=actor_type, actor_id=actor_id,
                     thread_id=thread["id"], message_id=message["id"], draft_id=draft_id,
                     detail={"flags": [f.id for f in flags]})

    _record_profile_changes(db, thread, message, draft_id, result.profile_update_requests,
                            actor_type=actor_type, actor_id=actor_id)
    return drafts_repo.by_id(db, draft_id)


def _record_profile_changes(db, thread, message, draft_id, extracted, *, actor_type, actor_id):
    """Merge model/mock-extracted profile changes with detector rows, deduped
    by field_hint for the same message."""
    existing_hints = {row["field_hint"] for row in profile_repo.for_message(db, message["id"])}
    for entry in extracted or []:
        hint = entry.get("field_hint", "other")
        if hint in existing_hints:
            continue
        existing_hints.add(hint)
        change_id = profile_repo.insert(
            db, thread_id=thread["id"], message_id=message["id"], draft_id=draft_id,
            field_hint=hint, requested_change=entry.get("requested_change", "Profile update"),
            quote=entry.get("quote", ""), source="model",
        )
        audit.record(db, "profile_change_noted", actor_type=actor_type, actor_id=actor_id,
                     thread_id=thread["id"], message_id=message["id"], draft_id=draft_id,
                     detail={"change_id": change_id, "field_hint": hint, "source": "model"})


def regenerate_draft(db: sqlite3.Connection, cfg: Config, draft_row, *, advisor_id: int) -> sqlite3.Row:
    from ..repos import threads as threads_repo

    states.check(states.REGENERATE, draft_row["status"])
    message = messages_repo.by_id(db, draft_row["in_reply_to_message_id"])
    if drafts_repo.approved_exists(db, message["id"]):
        raise states.InvalidTransition(states.REGENERATE, states.APPROVED_SENT)
    thread = threads_repo.by_id(db, draft_row["thread_id"])

    if draft_row["status"] in drafts_repo.ACTIVE_STATUSES:
        drafts_repo.set_status(db, draft_row["id"], states.SUPERSEDED)
    audit.record(db, "draft_regenerated", actor_type="advisor", actor_id=advisor_id,
                 thread_id=thread["id"], message_id=message["id"], draft_id=draft_row["id"],
                 detail={"superseded_version": draft_row["version"]})
    return create_draft_for_message(db, cfg, thread=thread, message=message,
                                    actor_type="advisor", actor_id=advisor_id)
