from conftest import db_conn, login, post_scenario


def test_default_scope_routes_complaints_personal(client, webhook_headers, cfg):
    body = post_scenario(client, webhook_headers, "daniel_complaint", external_id="scope-1").get_json()
    assert body["triage"] == "personal"
    assert body["draft_id"] is None
    with db_conn(cfg) as db:
        events = [r["event"] for r in db.execute(
            "SELECT event FROM audit_log WHERE message_id = ? ORDER BY id", (body["message_id"],))]
    assert "message_routed_personal" in events


def test_flip_to_all_drafts_complex_inbound_without_retroactive_drafting(client, webhook_headers, cfg):
    first = post_scenario(client, webhook_headers, "daniel_complaint", external_id="scope-first").get_json()
    assert first["draft_id"] is None

    login(client, "michael-trent")
    response = client.post("/api/settings/assist-scope", json={"assist_scope": "all"})
    assert response.status_code == 200

    second = post_scenario(client, webhook_headers, "daniel_complaint", external_id="scope-second").get_json()
    assert second["triage"] == "personal"
    assert second["draft_id"] is not None, "in all-inquiries scope, complex messages auto-draft too"

    with db_conn(cfg) as db:
        # No retroactive drafting: the first complaint still has no draft.
        n_first = db.execute("SELECT COUNT(*) AS n FROM drafts WHERE in_reply_to_message_id = ?",
                             (first["message_id"],)).fetchone()["n"]
        assert n_first == 0
        draft = db.execute("SELECT * FROM drafts WHERE id = ?", (second["draft_id"],)).fetchone()
        assert draft["intent"] == "complaint_or_escalation"
        flips = db.execute("SELECT * FROM audit_log WHERE event = 'assist_scope_changed'").fetchall()
        assert len(flips) == 1
        assert flips[0]["actor_type"] == "advisor"


def test_flip_back_restores_standard_behavior(client, webhook_headers, cfg):
    login(client, "michael-trent")
    client.post("/api/settings/assist-scope", json={"assist_scope": "all"})
    client.post("/api/settings/assist-scope", json={"assist_scope": "routine_only"})
    third = post_scenario(client, webhook_headers, "daniel_complaint", external_id="scope-third").get_json()
    assert third["draft_id"] is None


def test_scope_validation(client):
    login(client, "sarah-kline")
    assert client.post("/api/settings/assist-scope", json={"assist_scope": "everything"}).status_code == 422
    assert client.get("/api/settings/assist-scope").get_json()["assist_scope"] == "routine_only"
