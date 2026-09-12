from datetime import timedelta

from conftest import db_conn, login, post_scenario

from zadok.utils import now_dt, to_iso


def test_sla_aging_and_clear_on_send(client, webhook_headers, cfg):
    stale = to_iso(now_dt() - timedelta(hours=30))
    post_scenario(client, webhook_headers, "alex_status_checkin", external_id="sla-1", received_at=stale)

    login(client, "sarah-kline")
    threads = client.get("/api/threads").get_json()["threads"]
    alex = next(t for t in threads if t["client_display_name"] == "Alex Morgan")
    assert alex["waiting"]["overdue"] is True, "30h waiting must exceed the 24h SLA"
    assert alex["badge"] == "ready"

    detail = client.get(f"/api/threads/{alex['id']}").get_json()
    assert detail["waiting"]["overdue"] is True
    draft = detail["draft"]
    assert client.post(f"/api/drafts/{draft['id']}/approve", json={}).status_code == 200

    after = client.get(f"/api/threads/{alex['id']}").get_json()
    assert after["waiting"]["since"] is None
    assert after["messages"][-1]["direction"] == "outbound"


def test_fresh_message_is_not_overdue(client, webhook_headers):
    post_scenario(client, webhook_headers, "casey_pleasantry", external_id="sla-2")
    login(client, "sarah-kline")
    casey = next(t for t in client.get("/api/threads").get_json()["threads"]
                 if t["client_display_name"] == "Casey Bennett")
    assert casey["waiting"]["overdue"] is False


def test_draft_anyway_flow(client, webhook_headers, cfg):
    body = post_scenario(client, webhook_headers, "daniel_complaint", external_id="da-1").get_json()
    login(client, "michael-trent")

    detail = client.get(f"/api/threads/{body['thread_id']}").get_json()
    assert detail["draft"] is None
    assert detail["personal_pending"] is True

    response = client.post(f"/api/threads/{body['thread_id']}/draft")
    assert response.status_code == 201
    draft = response.get_json()["draft"]
    assert draft["intent"] == "complaint_or_escalation"

    # Second call returns the existing active draft rather than a new one.
    again = client.post(f"/api/threads/{body['thread_id']}/draft")
    assert again.status_code == 200
    assert again.get_json()["draft"]["id"] == draft["id"]

    with db_conn(cfg) as db:
        events = [r["event"] for r in db.execute(
            "SELECT event FROM audit_log WHERE draft_id = ? ORDER BY id", (draft["id"],))]
    assert "draft_requested_manually" in events


def test_regenerate_creates_version_chain(client, webhook_headers, cfg):
    body = post_scenario(client, webhook_headers, "alex_status_checkin", external_id="regen-1").get_json()
    login(client, "sarah-kline")
    detail = client.get(f"/api/threads/{body['thread_id']}").get_json()
    v1 = detail["draft"]

    response = client.post(f"/api/drafts/{v1['id']}/regenerate")
    assert response.status_code == 201
    v2 = response.get_json()["draft"]
    assert v2["version"] == 2
    assert v2["text"] != v1["text"], "variant rotation must produce a different draft"

    with db_conn(cfg) as db:
        old = db.execute("SELECT status FROM drafts WHERE id = ?", (v1["id"],)).fetchone()
        assert old["status"] == "superseded"

    # Old row is terminal now.
    assert client.post(f"/api/drafts/{v1['id']}/approve", json={}).status_code == 409


def test_ownership_is_enforced(client, webhook_headers):
    body = post_scenario(client, webhook_headers, "mia_appointment_with_profile_change",
                         external_id="own-1").get_json()
    login(client, "sarah-kline")  # not Mia's advisor
    assert client.get(f"/api/threads/{body['thread_id']}").status_code == 404
    assert client.post(f"/api/threads/{body['thread_id']}/draft").status_code == 404
    assert client.get("/api/threads").get_json()["threads"] == []


def test_api_requires_login(client, webhook_headers):
    assert client.get("/api/threads").status_code == 401
    assert client.get("/inbox").status_code == 302
