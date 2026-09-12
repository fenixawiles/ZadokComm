import pytest

from seeds.seed import seed_advisors
from zadok import create_app
from zadok.db import init_db, open_db

WEBHOOK_SECRET = "test-webhook"
PASSCODE = "test-pass"


@pytest.fixture
def app(tmp_path):
    overrides = {
        "APP_ENV": "test",
        "DATABASE_PATH": str(tmp_path / "test.db"),
        "SECRET_KEY": "test-secret",
        "WEBHOOK_SHARED_SECRET": WEBHOOK_SECRET,
        "DEV_PASSCODE": PASSCODE,
        "RESPONSE_SLA_HOURS": "24",
        "ZADOK_ASSIST_SCOPE_DEFAULT": "routine_only",
        "DRAFT_ENGINE": "mock",
        "CRM_CONNECTORS": "mock_salesforce,mock_woven",
        "ZADOK_ALLOW_LIVE_MODEL_CALLS": "0",
        "ZADOK_ALLOW_LIVE_SEND": "0",
        "OPENAI_API_KEY": "",
        "OUTBOUND_SENDER": "mock",
    }
    application = create_app(overrides)
    cfg = application.config["ZADOK"]
    with open_db(cfg.database_path) as db:
        init_db(db, cfg.assist_scope_default)
        seed_advisors(db)
    return application


@pytest.fixture
def cfg(app):
    return app.config["ZADOK"]


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def webhook_headers():
    return {"X-Zadok-Webhook-Token": WEBHOOK_SECRET}


def login(client, slug):
    response = client.post("/login", data={"advisor_slug": slug, "passcode": PASSCODE})
    assert response.status_code == 302
    return client


def post_scenario(client, headers, name, *, external_id=None, received_at=None):
    from zadok.inbound.scenarios import build_payload

    payload = build_payload(name, external_id=external_id or f"test-{name}", received_at=received_at)
    return client.post("/webhooks/inbound", json=payload, headers=headers)


def db_conn(cfg):
    return open_db(cfg.database_path)
