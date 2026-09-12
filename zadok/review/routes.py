"""Advisor-facing pages and JSON APIs: inbox, thread view, draft actions,
approve/send pipeline, profile-change cards, assist-scope toggle, audit drawer."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for

from .. import audit
from ..auth.decorators import current_advisor, login_required
from ..config import ASSIST_SCOPE_VALUES
from ..connectors import resolver
from ..db import get_db
from ..domain import states
from ..domain.intents import APPOINTMENT_REQUEST, PERSONAL
from ..drafting import service as drafting_service
from ..drafting.guardrails import final_scan
from ..outbound.sender import resolve_sender
from ..repos import drafts as drafts_repo
from ..repos import messages as messages_repo
from ..repos import profile_changes as profile_repo
from ..repos import sends as sends_repo
from ..repos import settings as settings_repo
from ..repos import threads as threads_repo
from ..utils import loads, now_dt, now_iso, parse_iso

bp = Blueprint("review", __name__)


# ---------------------------------------------------------------- pages

@bp.get("/")
def index():
    return redirect(url_for("review.inbox"))


@bp.get("/inbox")
@login_required
def inbox():
    return render_template("inbox.html", advisor=current_advisor(),
                           app_env=current_app.config["ZADOK"].app_env)


# ---------------------------------------------------------------- helpers

def _cfg():
    return current_app.config["ZADOK"]


def _own_thread_or_none(thread_id: int):
    thread = threads_repo.by_id(get_db(), thread_id)
    if thread is None or thread["assigned_advisor_id"] != current_advisor()["id"]:
        return None
    return thread


def _waiting_info(thread):
    since = thread["awaiting_reply_since"]
    if not since:
        return {"since": None, "hours": 0, "overdue": False}
    hours = max(0.0, (now_dt() - parse_iso(since)).total_seconds() / 3600)
    return {"since": since, "hours": round(hours, 1), "overdue": hours > _cfg().response_sla_hours}


def _active_draft_row(db, thread):
    latest = messages_repo.latest_inbound(db, thread["id"])
    if latest is None:
        return None, None
    active = drafts_repo.active_for_message(db, latest["id"])
    if active is None:
        # Surface a failed latest attempt so the UI can offer Regenerate.
        version = drafts_repo.latest_version(db, latest["id"])
        if version:
            row = db.execute(
                "SELECT * FROM drafts WHERE in_reply_to_message_id = ? AND version = ?",
                (latest["id"], version),
            ).fetchone()
            if row is not None and row["status"] == states.FAILED:
                return latest, row
    return latest, active


def _thread_badge(db, thread):
    latest, draft = _active_draft_row(db, thread)
    if draft is not None and draft["status"] == states.NEEDS_ATTENTION:
        return "needs_attention"
    if draft is not None and draft["status"] in (states.DRAFTED, states.EDITED):
        return "ready"
    if draft is not None and draft["status"] == states.FAILED:
        return "failed"
    if (latest is not None and latest["triage"] == PERSONAL
            and not drafts_repo.approved_exists(db, latest["id"]) and thread["awaiting_reply_since"]):
        return "personal"
    return None


def _draft_json(draft):
    if draft is None:
        return None
    flags = loads(draft["guardrail_flags_json"], [])
    return {
        "id": draft["id"],
        "version": draft["version"],
        "status": draft["status"],
        "outcome": draft["outcome"],
        "intent": draft["intent"],
        "engine": draft["engine"],
        "model_id": draft["model_id"],
        "text": drafts_repo.final_text(draft),
        "original_text": draft["draft_text"],
        "was_edited": bool(draft["edited_text"]),
        "flags": flags,
        "claims": loads(draft["claims_json"], []),
    }


def _context_pairs(db, thread, draft):
    """Collapsed-panel summary. Prefer the packet the draft actually saw; fall
    back to a live connector lookup for personal threads with no draft yet."""
    packet = loads(draft["context_packet_json"]) if draft is not None else None
    if packet is None:
        if thread["crm_source"] == "unknown":
            return [["CRM match", "No existing record"], ["Relationship", "First inquiry"]]
        record, _ = resolver.resolve_by_ref(resolver.build_connectors(_cfg()), thread["client_ref"])
        if record is None:
            return [["CRM match", "Record unavailable"]]
        packet = {
            "assigned_advisor_name": "", "relationship_summary": record.get("relationship_summary", ""),
            "expressed_interests": record.get("expressed_interests", []),
            "purchase_history_summary": record.get("purchase_history_summary", ""),
            "last_visit_summary": record.get("last_visit_summary", ""),
        }
    pairs = []
    if thread["crm_source"] == "unknown":
        pairs.append(["CRM match", "No existing record"])
    labels = [
        ("assigned_advisor_name", "Advisor"),
        ("relationship_summary", "Relationship"),
        ("expressed_interests", "Interest"),
        ("purchase_history_summary", "History"),
        ("last_visit_summary", "Last visit"),
        ("last_contact_summary", "Last contact"),
    ]
    for key, label in labels:
        value = packet.get(key)
        if isinstance(value, list):
            value = ", ".join(value)
        if value:
            pairs.append([label, value])
    return pairs


# ---------------------------------------------------------------- thread APIs

@bp.get("/api/threads")
@login_required
def api_threads():
    db = get_db()
    advisor = current_advisor()
    rows = []
    for thread in threads_repo.for_advisor(db, advisor["id"]):
        latest = messages_repo.latest_inbound(db, thread["id"])
        rows.append({
            "id": thread["id"],
            "client_display_name": thread["client_display_name"],
            "crm_source": thread["crm_source"],
            "snippet": (latest["body"][:80] if latest else ""),
            "last_inbound_at": thread["last_inbound_at"],
            "badge": _thread_badge(db, thread),
            "waiting": _waiting_info(thread),
        })
    # Action first: unanswered before answered, oldest wait first.
    rows.sort(key=lambda r: (r["waiting"]["since"] is None, r["waiting"]["since"] or "", r["id"]))
    return jsonify({"threads": rows, "assist_scope": settings_repo.get(db, "assist_scope",
                                                                       _cfg().assist_scope_default)})


@bp.get("/api/threads/<int:thread_id>")
@login_required
def api_thread(thread_id: int):
    db = get_db()
    thread = _own_thread_or_none(thread_id)
    if thread is None:
        return jsonify({"error": "not found"}), 404
    latest, draft = _active_draft_row(db, thread)
    packet = loads(draft["context_packet_json"]) if draft is not None else None

    schedule_note = None
    if draft is not None and draft["intent"] == APPOINTMENT_REQUEST and packet and packet.get("appointment_slots"):
        advisor = current_advisor()
        schedule_note = f"{advisor['display_name'].split(' ')[0]} is available " + \
            " and ".join(packet["appointment_slots"]) + "."

    personal_pending = (
        latest is not None and latest["triage"] == PERSONAL and draft is None
        and not drafts_repo.approved_exists(db, latest["id"])
    )
    return jsonify({
        "thread": {
            "id": thread["id"],
            "client_display_name": thread["client_display_name"],
            "subtitle": ("New customer · " if thread["crm_source"] == "unknown" else "Existing client · ")
            + thread["channel"].capitalize(),
            "crm_source": thread["crm_source"],
        },
        "messages": [
            {"id": m["id"], "direction": m["direction"], "sender": m["sender_display"],
             "body": m["body"], "occurred_at": m["occurred_at"], "triage": m["triage"]}
            for m in messages_repo.for_thread(db, thread["id"])
        ],
        "context": _context_pairs(db, thread, draft),
        "draft": _draft_json(draft),
        "personal_pending": personal_pending,
        "schedule_note": schedule_note,
        "profile_changes": [
            {"id": c["id"], "field_hint": c["field_hint"], "requested_change": c["requested_change"],
             "quote": c["quote"], "source": c["source"]}
            for c in profile_repo.open_for_thread(db, thread["id"])
        ],
        "waiting": _waiting_info(thread),
    })


@bp.get("/api/threads/<int:thread_id>/audit")
@login_required
def api_thread_audit(thread_id: int):
    db = get_db()
    thread = _own_thread_or_none(thread_id)
    if thread is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"events": [
        {"occurred_at": row["occurred_at"], "event": row["event"], "actor_type": row["actor_type"],
         "detail": loads(row["detail_json"])}
        for row in audit.for_thread(db, thread_id)
    ]})


@bp.post("/api/threads/<int:thread_id>/draft")
@login_required
def api_draft_anyway(thread_id: int):
    """Draft anyway — manual drafting for a personal-routed message."""
    db = get_db()
    cfg = _cfg()
    thread = _own_thread_or_none(thread_id)
    if thread is None:
        return jsonify({"error": "not found"}), 404
    latest = messages_repo.latest_inbound(db, thread["id"])
    if latest is None:
        return jsonify({"error": "no inbound message to draft against"}), 409
    if drafts_repo.approved_exists(db, latest["id"]):
        return jsonify({"error": "a reply was already sent for this message"}), 409
    existing = drafts_repo.active_for_message(db, latest["id"])
    if existing is not None:
        return jsonify({"draft": _draft_json(existing)})
    advisor = current_advisor()
    draft = drafting_service.create_draft_for_message(
        db, cfg, thread=thread, message=latest, actor_type="advisor", actor_id=advisor["id"], manual=True,
    )
    db.commit()
    return jsonify({"draft": _draft_json(draft)}), 201


# ---------------------------------------------------------------- draft actions

def _own_draft_or_none(draft_id: int):
    db = get_db()
    draft = drafts_repo.by_id(db, draft_id)
    if draft is None:
        return None, None
    thread = threads_repo.by_id(db, draft["thread_id"])
    if thread["assigned_advisor_id"] != current_advisor()["id"]:
        return None, None
    return draft, thread


@bp.post("/api/drafts/<int:draft_id>/edit")
@login_required
def api_edit(draft_id: int):
    db = get_db()
    draft, thread = _own_draft_or_none(draft_id)
    if draft is None:
        return jsonify({"error": "not found"}), 404
    text = (request.get_json(silent=True) or {}).get("text", "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 422
    try:
        states.check(states.EDIT, draft["status"])
    except states.InvalidTransition as exc:
        return jsonify({"error": str(exc)}), 409
    advisor = current_advisor()
    drafts_repo.set_edited(db, draft_id, text, advisor["id"])
    audit.record(db, "draft_edited", actor_type="advisor", actor_id=advisor["id"],
                 thread_id=thread["id"], message_id=draft["in_reply_to_message_id"], draft_id=draft_id,
                 detail={"length": len(text)})
    db.commit()
    return jsonify({"draft": _draft_json(drafts_repo.by_id(db, draft_id))})


@bp.post("/api/drafts/<int:draft_id>/regenerate")
@login_required
def api_regenerate(draft_id: int):
    db = get_db()
    cfg = _cfg()
    draft, thread = _own_draft_or_none(draft_id)
    if draft is None:
        return jsonify({"error": "not found"}), 404
    advisor = current_advisor()
    try:
        new_draft = drafting_service.regenerate_draft(db, cfg, draft, advisor_id=advisor["id"])
    except states.InvalidTransition as exc:
        return jsonify({"error": str(exc)}), 409
    db.commit()
    return jsonify({"draft": _draft_json(new_draft)}), 201


@bp.post("/api/drafts/<int:draft_id>/discard")
@login_required
def api_discard(draft_id: int):
    db = get_db()
    draft, thread = _own_draft_or_none(draft_id)
    if draft is None:
        return jsonify({"error": "not found"}), 404
    try:
        states.check(states.DISCARD, draft["status"])
    except states.InvalidTransition as exc:
        return jsonify({"error": str(exc)}), 409
    advisor = current_advisor()
    drafts_repo.set_status(db, draft_id, states.DISCARDED)
    audit.record(db, "draft_discarded", actor_type="advisor", actor_id=advisor["id"],
                 thread_id=thread["id"], message_id=draft["in_reply_to_message_id"], draft_id=draft_id)
    db.commit()
    return jsonify({"ok": True})


@bp.post("/api/drafts/<int:draft_id>/approve")
@login_required
def api_approve(draft_id: int):
    """Approve + send: transition check -> final deterministic scan (advisor
    edits can violate too) -> acknowledgment gate -> sender -> records."""
    db = get_db()
    cfg = _cfg()
    draft, thread = _own_draft_or_none(draft_id)
    if draft is None:
        return jsonify({"error": "not found"}), 404
    try:
        states.check(states.APPROVE, draft["status"])
    except states.InvalidTransition as exc:
        return jsonify({"error": str(exc)}), 409
    if drafts_repo.approved_exists(db, draft["in_reply_to_message_id"]):
        return jsonify({"error": "a reply was already sent for this message"}), 409

    advisor = current_advisor()
    final_text = drafts_repo.final_text(draft)
    flags = final_scan(final_text)
    acknowledge = bool((request.get_json(silent=True) or {}).get("acknowledge_flags"))
    if flags and not acknowledge:
        return jsonify({"error": "flags_require_acknowledgment",
                        "flags": [f.to_dict() for f in flags]}), 409
    if flags:
        audit.record(db, "flags_acknowledged", actor_type="advisor", actor_id=advisor["id"],
                     thread_id=thread["id"], message_id=draft["in_reply_to_message_id"],
                     draft_id=draft_id, detail={"flags": [f.id for f in flags]})

    sender = resolve_sender(cfg)
    external_ref = sender.send(thread, final_text, advisor)
    outbound_id = messages_repo.insert(
        db, thread_id=thread["id"], direction="outbound", source="shell",
        external_message_id=f"send-{draft_id}", sender_display=advisor["sign_off_name"],
        body=final_text, occurred_at=now_iso(),
    )
    sends_repo.insert(
        db, draft_id=draft_id, thread_id=thread["id"], outbound_message_id=outbound_id,
        sent_text=final_text, was_edited=bool(draft["edited_text"]),
        final_scan_flags=[f.to_dict() for f in flags], flags_acknowledged=bool(flags),
        sender_impl=sender.name, external_send_ref=external_ref, sent_by_advisor_id=advisor["id"],
    )
    drafts_repo.set_status(db, draft_id, states.APPROVED_SENT)
    threads_repo.clear_awaiting(db, thread["id"])
    audit.record(db, "draft_approved", actor_type="advisor", actor_id=advisor["id"],
                 thread_id=thread["id"], message_id=draft["in_reply_to_message_id"], draft_id=draft_id,
                 detail={"was_edited": bool(draft["edited_text"])})
    audit.record(db, "send_recorded", actor_type="advisor", actor_id=advisor["id"],
                 thread_id=thread["id"], message_id=outbound_id, draft_id=draft_id,
                 detail={"sender_impl": sender.name, "external_send_ref": external_ref})
    db.commit()
    return jsonify({"sent": True, "external_send_ref": external_ref, "sender_impl": sender.name})


# ---------------------------------------------------------------- profile changes

@bp.post("/api/profile-changes/<int:change_id>/<string:action>")
@login_required
def api_profile_change(change_id: int, action: str):
    if action not in ("acknowledge", "dismiss"):
        return jsonify({"error": "unknown action"}), 404
    db = get_db()
    row = profile_repo.by_id(db, change_id)
    if row is None:
        return jsonify({"error": "not found"}), 404
    thread = threads_repo.by_id(db, row["thread_id"])
    if thread["assigned_advisor_id"] != current_advisor()["id"]:
        return jsonify({"error": "not found"}), 404
    if row["status"] != "open":
        return jsonify({"error": "already resolved"}), 409
    advisor = current_advisor()
    status = "acknowledged" if action == "acknowledge" else "dismissed"
    profile_repo.resolve(db, change_id, status=status, advisor_id=advisor["id"])
    audit.record(db, f"profile_change_{status}", actor_type="advisor", actor_id=advisor["id"],
                 thread_id=thread["id"], message_id=row["message_id"],
                 detail={"change_id": change_id, "field_hint": row["field_hint"]})
    db.commit()
    return jsonify({"ok": True, "status": status})


# ---------------------------------------------------------------- settings

@bp.get("/api/settings/assist-scope")
@login_required
def api_get_scope():
    db = get_db()
    return jsonify({"assist_scope": settings_repo.get(db, "assist_scope", _cfg().assist_scope_default)})


@bp.post("/api/settings/assist-scope")
@login_required
def api_set_scope():
    value = (request.get_json(silent=True) or {}).get("assist_scope", "")
    if value not in ASSIST_SCOPE_VALUES:
        return jsonify({"error": f"assist_scope must be one of {list(ASSIST_SCOPE_VALUES)}"}), 422
    db = get_db()
    advisor = current_advisor()
    old = settings_repo.get(db, "assist_scope", _cfg().assist_scope_default)
    settings_repo.put(db, "assist_scope", value, advisor["id"])
    audit.record(db, "assist_scope_changed", actor_type="advisor", actor_id=advisor["id"],
                 detail={"from": old, "to": value})
    db.commit()
    return jsonify({"assist_scope": value})
