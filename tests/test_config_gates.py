import pytest

from zadok.config import Config, ConfigError
from zadok.drafting.service import resolve_engine
from zadok.outbound.sender import resolve_sender

BASE = {
    "APP_ENV": "test",
    "SECRET_KEY": "s",
    "WEBHOOK_SHARED_SECRET": "w",
    "DATABASE_PATH": ":memory:",
}


def make(**extra):
    return Config.from_env({**BASE, **extra})


def test_stray_key_with_gate_off_cannot_spend():
    cfg = make(OPENAI_API_KEY="sk-stray", ZADOK_ALLOW_LIVE_MODEL_CALLS="0", DRAFT_ENGINE="openai")
    assert cfg.effective_openai_api_key is None
    assert resolve_engine(cfg).name == "mock"


def test_gate_on_without_key_still_mock():
    cfg = make(OPENAI_API_KEY="", ZADOK_ALLOW_LIVE_MODEL_CALLS="1", DRAFT_ENGINE="openai")
    assert resolve_engine(cfg).name == "mock"


def test_gate_and_key_but_mock_engine_choice_still_mock():
    cfg = make(OPENAI_API_KEY="sk-x", ZADOK_ALLOW_LIVE_MODEL_CALLS="1", DRAFT_ENGINE="mock")
    assert resolve_engine(cfg).name == "mock"


def test_unknown_app_env_fails_safe_to_production():
    cfg = make(APP_ENV="prouction")  # typo on purpose
    assert cfg.is_production is True
    with pytest.raises(ConfigError):
        cfg.validate_for_boot()


def test_production_boot_refusals():
    cfg = make(APP_ENV="production", SECRET_KEY="", WEBHOOK_SHARED_SECRET="")
    with pytest.raises(ConfigError, match="SECRET_KEY"):
        cfg.validate_for_boot()
    # Even fully configured, production refuses while auth is the dev shell.
    cfg2 = make(APP_ENV="production", SECRET_KEY="x", WEBHOOK_SHARED_SECRET="y")
    with pytest.raises(ConfigError, match="SSO"):
        cfg2.validate_for_boot()


def test_non_mock_sender_requires_live_send_gate():
    cfg = make(OUTBOUND_SENDER="salesforce", ZADOK_ALLOW_LIVE_SEND="0")
    with pytest.raises(ConfigError, match="ZADOK_ALLOW_LIVE_SEND"):
        cfg.validate_for_boot()
    with pytest.raises(ConfigError):
        resolve_sender(cfg)


def test_mock_sender_needs_no_gate():
    cfg = make()
    assert resolve_sender(cfg).name == "mock"


def test_invalid_scope_default_rejected():
    with pytest.raises(ConfigError):
        make(ZADOK_ASSIST_SCOPE_DEFAULT="everything")
