import json

from conftest import db_conn, post_scenario

from zadok.inbound.scenarios import build_payload


def test_rejects_missing_or_wrong_token(client):
    payload = build_payload("alex_status_checkin", external_id="tok-1")
    assert client.post("/webhooks/inbound", json=payload).status_code == 401
    assert client.post("/webhooks/inbound", json=payload,
                       headers={"X-Zadok-Webhook-Token": "wrong"}).status_code == 401


def test_rejects_malformed_payload(client, webhook_headers):
    response = client.post("/webhooks/inbound", json={"source": "x"}, headers=webhook_headers)
    assert response.status_code == 422
    assert "problems" in response.get_json()


def test_happy_path_creates_thread_message_and_draft(client, webhook_headers, cfg):
    response = post_scenario(client, webhook_headers, "alex_status_checkin", external_id="hook-1")
    assert response.status_code == 201
    body = response.get_json()
    assert body["duplicate"] is False
    assert body["draft_id"] is not None
    assert body["triage"] == "routine"
    with db_conn(cfg) as db:
        draft = db.execute("SELECT * FROM drafts WHERE id = ?", (body["draft_id"],)).fetchone()
        assert draft["status"] == "drafted"
        assert draft["engine"] == "mock"
        assert draft["model_registry_fingerprint"]


def test_exact_replay_is_idempotent(client, webhook_headers, cfg):
    first = post_scenario(client, webhook_headers, "alex_status_checkin", external_id="hook-replay").get_json()
    replay = post_scenario(client, webhook_headers, "alex_status_checkin", external_id="hook-replay")
    assert replay.status_code == 200
    body = replay.get_json()
    assert body["duplicate"] is True
    assert body["message_id"] == first["message_id"]
    with db_conn(cfg) as db:
        count = db.execute("SELECT COUNT(*) AS n FROM drafts WHERE in_reply_to_message_id = ?",
                           (first["message_id"],)).fetchone()["n"]
        assert count == 1
        events = [r["event"] for r in db.execute(
            "SELECT event FROM audit_log WHERE message_id = ? ORDER BY id", (first["message_id"],))]
        assert "inbound_duplicate_ignored" in events


def test_unknown_sender_routes_to_new_client_team(client, webhook_headers, cfg):
    body = post_scenario(client, webhook_headers, "jordan_new_prospect", external_id="hook-jordan").get_json()
    with db_conn(cfg) as db:
        thread = db.execute("SELECT * FROM threads WHERE id = ?", (body["thread_id"],)).fetchone()
        advisor = db.execute("SELECT * FROM advisors WHERE id = ?", (thread["assigned_advisor_id"],)).fetchone()
        assert thread["crm_source"] == "unknown"
        assert thread["client_ref"].startswith("unknown:")
        assert advisor["role"] == "new_client_team"
        draft = db.execute("SELECT * FROM drafts WHERE thread_id = ?", (thread["id"],)).fetchone()
        assert draft is not None  # new prospects are routine: the welcome reply drafts automatically
        packet = json.loads(draft["context_packet_json"])
        assert packet["client_status"] == "new_prospect"
