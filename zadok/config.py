"""Single environment chokepoint.

Every environment variable the application reads is read here, once, into an
immutable Config. Two properties are load-bearing:

- IS_PRODUCTION fails safe: any APP_ENV value that is not a known development
  name is treated as production, so a typo tightens rather than loosens.
- Live side effects are gated. The raw OPENAI_API_KEY is never exported;
  `effective_openai_api_key` is None unless ZADOK_ALLOW_LIVE_MODEL_CALLS=1,
  so a stray key in the environment can never cause spend. The same shape
  guards outbound sending via ZADOK_ALLOW_LIVE_SEND.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

NON_PRODUCTION_ENVS = frozenset({"development", "dev", "local", "test", "testing", ""})
ASSIST_SCOPE_VALUES = ("routine_only", "all")


class ConfigError(RuntimeError):
    """Raised at boot when the configuration is unsafe to run."""


def _flag(value: str | None) -> bool:
    return (value or "").strip() == "1"


@dataclass(frozen=True)
class Config:
    app_env: str
    is_production: bool
    secret_key: str
    webhook_shared_secret: str
    dev_passcode: str
    database_path: str
    draft_engine: str
    crm_connectors: tuple[str, ...]
    response_sla_hours: int
    assist_scope_default: str
    max_draft_output_tokens: int
    allow_live_model_calls: bool
    allow_live_send: bool
    effective_openai_api_key: str | None
    outbound_sender: str

    @classmethod
    def from_env(cls, overrides: dict | None = None) -> "Config":
        load_dotenv()
        env = dict(os.environ)
        if overrides:
            env.update({k: str(v) for k, v in overrides.items()})

        app_env = env.get("APP_ENV", "development").strip().lower()
        is_production = app_env not in NON_PRODUCTION_ENVS

        allow_model_calls = _flag(env.get("ZADOK_ALLOW_LIVE_MODEL_CALLS"))
        raw_key = env.get("OPENAI_API_KEY", "").strip()
        effective_key = raw_key if (allow_model_calls and raw_key) else None

        scope_default = env.get("ZADOK_ASSIST_SCOPE_DEFAULT", "routine_only").strip()
        if scope_default not in ASSIST_SCOPE_VALUES:
            raise ConfigError(
                f"ZADOK_ASSIST_SCOPE_DEFAULT must be one of {ASSIST_SCOPE_VALUES}, got {scope_default!r}"
            )

        return cls(
            app_env=app_env,
            is_production=is_production,
            secret_key=env.get("SECRET_KEY", "").strip() or ("" if is_production else "dev-secret-key"),
            webhook_shared_secret=env.get("WEBHOOK_SHARED_SECRET", "").strip()
            or ("" if is_production else "dev-webhook-secret"),
            dev_passcode=env.get("DEV_PASSCODE", "").strip() or "zadok-dev",
            database_path=env.get("DATABASE_PATH", "./zadok.db").strip(),
            draft_engine=env.get("DRAFT_ENGINE", "mock").strip().lower(),
            crm_connectors=tuple(
                name.strip()
                for name in env.get("CRM_CONNECTORS", "mock_salesforce,mock_woven").split(",")
                if name.strip()
            ),
            response_sla_hours=max(1, int(env.get("RESPONSE_SLA_HOURS", "24"))),
            assist_scope_default=scope_default,
            max_draft_output_tokens=max(200, int(env.get("MAX_DRAFT_OUTPUT_TOKENS", "1200"))),
            allow_live_model_calls=allow_model_calls,
            allow_live_send=_flag(env.get("ZADOK_ALLOW_LIVE_SEND")),
            effective_openai_api_key=effective_key,
            outbound_sender=env.get("OUTBOUND_SENDER", "mock").strip().lower(),
        )

    def validate_for_boot(self) -> None:
        if self.draft_engine not in ("mock", "openai"):
            raise ConfigError(f"DRAFT_ENGINE must be 'mock' or 'openai', got {self.draft_engine!r}")
        if self.outbound_sender != "mock" and not self.allow_live_send:
            raise ConfigError(
                "A non-mock outbound sender requires ZADOK_ALLOW_LIVE_SEND=1. "
                "This gate exists so nothing can ever send to a real client by accident."
            )
        if self.is_production:
            missing = [
                name
                for name, value in (("SECRET_KEY", self.secret_key), ("WEBHOOK_SHARED_SECRET", self.webhook_shared_secret))
                if not value
            ]
            if missing:
                raise ConfigError(f"Refusing to boot in production without: {', '.join(missing)}")
            # The pick-a-rep login is a development shell, not authentication.
            raise ConfigError(
                "Refusing to boot in production: the shell ships development-only auth. "
                "Real deployment requires SSO / real authentication first."
            )
