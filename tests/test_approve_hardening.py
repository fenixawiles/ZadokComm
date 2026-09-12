"""Regression tests for the approve-path findings from the PR #1 review:
stored draft-time flags must gate sends, empty drafts must never send, and a
draft goes stale the moment a newer inbound message reaches its thread."""
import json

from conftest import db_conn, login, post_scenario


def _flag_rows(flag_id):
    return json.dumps([{"id": flag_id, "label": f"test:{flag_id}", "matched_span": ""}])


def test_stored_nonreproducible_flags_still_require_acknowledgment(client, webhook_headers, cfg):
    body = post_scenario(client, webhook_headers, "alex_status_checkin", external_id="hard-1").get_json()
    # Simulate a draft flagged ONLY by checks the final text scan cannot
    # re-derive (an unsupported claim), with otherwise compliant text.
    with db_conn(cfg) as db:
        db.execute("UPDATE drafts SET status = 'needs_attention', guardrail_flags_json = ? WHERE id = ?",
                   (_flag_rows("unsupported_claim"), body["draft_id"]))

    login(client, "sarah-kline")
    refused = client.post(f"/api/drafts/{body['draft_id']}/approve", json={})
    assert refused.status_code == 409
    assert refused.get_json()["error"] == "flags_require_acknowledgment"
    assert "unsupported_claim" in {f["id"] for f in refused.get_json()["flags"]}

    accepted = client.post(f"/api/drafts/{body['draft_id']}/approve", json={"acknowledge_flags": True})
    assert accepted.status_code == 200
    with db_conn(cfg) as db:
        send = db.execute("SELECT * FROM sends WHERE draft_id = ?", (body["draft_id"],)).fetchone()
        assert send["flags_acknowledged"] == 1


def test_edited_draft_supersedes_stored_flags_but_not_content_scan(client, webhook_headers, cfg):
    body = post_scenario(client, webhook_headers, "alex_status_checkin", external_id="hard-2").get_json()
    with db_conn(cfg) as db:
        db.execute("UPDATE drafts SET status = 'needs_attention', guardrail_flags_json = ? WHERE id = ?",
                   (_flag_rows("wrong_signoff"), body["draft_id"]))
    login(client, "sarah-kline")
    # The advisor rewrites the draft: stored provenance flags no longer apply...
    client.post(f"/api/drafts/{body['draft_id']}/edit",
                json={"text": "Hi Alex,\n\nAll noted — I'll be in touch personally.\n\nSarah"})
    assert client.post(f"/api/drafts/{body['draft_id']}/approve", json={}).status_code == 200


def test_empty_draft_is_never_sendable_even_acknowledged(client, webhook_headers, cfg):
    body = post_scenario(client, webhook_headers, "alex_status_checkin", external_id="hard-3").get_json()
    with db_conn(cfg) as db:
        db.execute("UPDATE drafts SET draft_text = '', status = 'needs_attention',"
                   " guardrail_flags_json = ? WHERE id = ?",
                   (_flag_rows("wrong_signoff"), body["draft_id"]))
    login(client, "sarah-kline")
    refused = client.post(f"/api/drafts/{body['draft_id']}/approve", json={"acknowledge_flags": True})
    assert refused.status_code == 409
    assert refused.get_json()["error"] == "empty_reply"


def test_stale_draft_rejected_after_newer_inbound(client, webhook_headers, cfg):
    first = post_scenario(client, webhook_headers, "alex_status_checkin", external_id="stale-1").get_json()
    second = post_scenario(client, webhook_headers, "alex_status_checkin", external_id="stale-2").get_json()
    assert first["thread_id"] == second["thread_id"]

    login(client, "sarah-kline")
    refused = client.post(f"/api/drafts/{first['draft_id']}/approve", json={})
    assert refused.status_code == 409
    assert refused.get_json()["error"] == "newer_message_arrived"

    # The draft for the latest message sends normally and clears the SLA clock.
    assert client.post(f"/api/drafts/{second['draft_id']}/approve", json={}).status_code == 200
    detail = client.get(f"/api/threads/{first['thread_id']}").get_json()
    assert detail["waiting"]["since"] is None

    with db_conn(cfg) as db:
        stale = db.execute("SELECT status FROM drafts WHERE id = ?", (first["draft_id"],)).fetchone()
    assert stale["status"] != "approved_sent"
