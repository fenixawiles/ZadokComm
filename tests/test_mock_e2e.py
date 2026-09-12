"""Full loop through the Flask test client in mock mode: no network, no key."""
from conftest import db_conn, login, post_scenario


def test_full_loop_appointment_with_profile_change(client, webhook_headers, cfg):
    body = post_scenario(client, webhook_headers, "mia_appointment_with_profile_change",
                         external_id="e2e-mia").get_json()
    login(client, "elena-ruiz")

    detail = client.get(f"/api/threads/{body['thread_id']}").get_json()
    draft = detail["draft"]
    assert draft["status"] == "drafted"
    assert "Saturday 10:30 AM" in detail["schedule_note"]
    assert detail["profile_changes"][0]["field_hint"] == "phone"
    assert detail["context"], "silent context panel must have content"

    edited_text = draft["text"].replace("Hi Mia", "Dear Mia")
    assert client.post(f"/api/drafts/{draft['id']}/edit",
                       json={"text": edited_text}).status_code == 200
    approve = client.post(f"/api/drafts/{draft['id']}/approve", json={})
    assert approve.status_code == 200
    assert approve.get_json()["sender_impl"] == "mock"

    with db_conn(cfg) as db:
        send = db.execute("SELECT * FROM sends WHERE draft_id = ?", (draft["id"],)).fetchone()
        assert send["was_edited"] == 1
        assert send["sent_text"] == edited_text.strip()  # the edit endpoint normalizes whitespace
        assert send["external_send_ref"].startswith("mock-")
        outbound = db.execute("SELECT * FROM messages WHERE id = ?",
                              (send["outbound_message_id"],)).fetchone()
        assert outbound["direction"] == "outbound"
        events = [r["event"] for r in db.execute(
            "SELECT event FROM audit_log WHERE thread_id = ? ORDER BY id", (body["thread_id"],))]

    expected_order = ["inbound_received", "client_resolved", "profile_change_noted",
                      "draft_created", "draft_edited", "draft_approved", "send_recorded"]
    positions = [events.index(e) for e in expected_order]
    assert positions == sorted(positions), f"audit order broken: {events}"

    # The message is answered: approving again (any draft of it) must fail.
    assert client.post(f"/api/drafts/{draft['id']}/approve", json={}).status_code == 409


def test_policy_stress_requires_acknowledged_send(client, webhook_headers, cfg):
    body = post_scenario(client, webhook_headers, "policy_stress", external_id="e2e-stress").get_json()
    login(client, "michael-trent")

    detail = client.get(f"/api/threads/{body['thread_id']}").get_json()
    draft = detail["draft"]
    assert draft["status"] == "needs_attention"
    flag_ids = {f["id"] for f in draft["flags"]}
    assert {"availability_confirmed", "delivery_promise", "discount_talk"} <= flag_ids

    refused = client.post(f"/api/drafts/{draft['id']}/approve", json={})
    assert refused.status_code == 409
    assert refused.get_json()["error"] == "flags_require_acknowledgment"
    assert refused.get_json()["flags"], "the 409 must carry the flags for the confirm dialog"

    accepted = client.post(f"/api/drafts/{draft['id']}/approve", json={"acknowledge_flags": True})
    assert accepted.status_code == 200

    with db_conn(cfg) as db:
        send = db.execute("SELECT * FROM sends WHERE draft_id = ?", (draft["id"],)).fetchone()
        assert send["flags_acknowledged"] == 1
        events = [r["event"] for r in db.execute(
            "SELECT event FROM audit_log WHERE thread_id = ? ORDER BY id", (body["thread_id"],))]
    assert "flags_acknowledged" in events


def test_advisor_edit_that_violates_is_caught_at_send(client, webhook_headers, cfg):
    """The final scan runs on the advisor's text too, not just the model's."""
    body = post_scenario(client, webhook_headers, "alex_status_checkin", external_id="e2e-edit").get_json()
    login(client, "sarah-kline")
    detail = client.get(f"/api/threads/{body['thread_id']}").get_json()
    draft = detail["draft"]
    assert draft["flags"] == []

    client.post(f"/api/drafts/{draft['id']}/edit",
                json={"text": "Hi Alex,\n\nGood news, it's in stock — come get it.\n\nSarah"})
    refused = client.post(f"/api/drafts/{draft['id']}/approve", json={})
    assert refused.status_code == 409
    assert "availability_confirmed" in {f["id"] for f in refused.get_json()["flags"]}


def test_healthz_reports_offline_posture(client):
    body = client.get("/healthz").get_json()
    assert body["engine"] == "mock"
    assert body["live_model_calls_enabled"] is False
    assert body["live_send_enabled"] is False
    assert body["protocol_pack_hash"]
    assert body["model_fingerprint"]
