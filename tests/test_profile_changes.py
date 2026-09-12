from conftest import db_conn, login, post_scenario

from zadok.domain.intents import detect_profile_changes


def test_detector_patterns():
    phone = detect_profile_changes("Quick note — my new number is (713) 555-0142, use that one.")
    assert [f["field_hint"] for f in phone] == ["phone"]
    assert "555-0142" in phone[0]["quote"]

    email = detect_profile_changes("Please email me at alex.new@example.com from now on.")
    assert [f["field_hint"] for f in email] == ["email"]

    interest = detect_profile_changes("Actually I'm now interested in the white-dial Daytona instead.")
    assert [f["field_hint"] for f in interest] == ["interest"]

    nothing = detect_profile_changes("Any updates on my watch?")
    assert nothing == []


def test_mia_scenario_yields_one_deduped_card(client, webhook_headers, cfg):
    """Detector and mock-engine extraction both see the phone change; the
    merge must keep exactly one card."""
    body = post_scenario(client, webhook_headers, "mia_appointment_with_profile_change",
                         external_id="pc-1").get_json()
    with db_conn(cfg) as db:
        rows = db.execute("SELECT * FROM profile_change_requests WHERE message_id = ?",
                          (body["message_id"],)).fetchall()
    assert len(rows) == 1
    assert rows[0]["field_hint"] == "phone"
    assert rows[0]["status"] == "open"


def test_acknowledge_and_dismiss_endpoints(client, webhook_headers, cfg):
    post_scenario(client, webhook_headers, "mia_appointment_with_profile_change", external_id="pc-2")
    login(client, "elena-ruiz")
    threads = client.get("/api/threads").get_json()["threads"]
    detail = client.get(f"/api/threads/{threads[0]['id']}").get_json()
    card = detail["profile_changes"][0]

    response = client.post(f"/api/profile-changes/{card['id']}/acknowledge")
    assert response.status_code == 200
    assert response.get_json()["status"] == "acknowledged"

    # Resolving twice is refused.
    assert client.post(f"/api/profile-changes/{card['id']}/dismiss").status_code == 409

    with db_conn(cfg) as db:
        events = [r["event"] for r in db.execute(
            "SELECT event FROM audit_log WHERE event LIKE 'profile_change%' ORDER BY id")]
    assert events == ["profile_change_noted", "profile_change_acknowledged"]


def test_other_advisor_cannot_touch_the_card(client, webhook_headers):
    post_scenario(client, webhook_headers, "mia_appointment_with_profile_change", external_id="pc-3")
    login(client, "sarah-kline")  # Mia belongs to Elena
    # Sarah can't even discover the card id through the thread API; probing ids directly 404s.
    assert client.post("/api/profile-changes/1/acknowledge").status_code == 404
