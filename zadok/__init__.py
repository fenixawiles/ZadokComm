"""Application factory + CLI commands."""
from __future__ import annotations

import click
from flask import Flask, jsonify

from .config import Config
from .db import close_db, init_db, open_db
from .model_registry import get_artifact, registry_fingerprint
from .protocols.loader import current_pack_hash


def create_app(overrides: dict | None = None) -> Flask:
    cfg = Config.from_env(overrides)
    cfg.validate_for_boot()

    app = Flask(__name__)
    app.secret_key = cfg.secret_key
    app.config["ZADOK"] = cfg
    app.teardown_appcontext(close_db)

    from .auth.routes import bp as auth_bp
    from .inbound.routes import bp as webhooks_bp
    from .inbound.simulator import bp as devtools_bp
    from .review.routes import bp as review_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(webhooks_bp)
    if not cfg.is_production:
        app.register_blueprint(devtools_bp)

    @app.get("/healthz")
    def healthz():
        from .db import get_db
        from .drafting.service import resolve_engine

        try:
            get_db().execute("SELECT 1")
            db_status = "ok"
        except Exception as exc:  # e.g. init-db not run yet
            db_status = f"error: {exc}"
        return jsonify({
            "status": "ok",
            "app_env": cfg.app_env,
            "db": db_status,
            "engine": resolve_engine(cfg).name,
            "live_model_calls_enabled": cfg.allow_live_model_calls,
            "live_send_enabled": cfg.allow_live_send,
            "protocol_pack_hash": current_pack_hash(),
            "model_fingerprint": registry_fingerprint(),
            "pinned_draft_model": get_artifact("draft").model_id,
        })

    # ------------------------------------------------------------- CLI

    @app.cli.command("init-db")
    def init_db_command():
        """Create the schema and seed runtime settings."""
        with open_db(cfg.database_path) as db:
            init_db(db, cfg.assist_scope_default)
        click.echo(f"Initialized {cfg.database_path} (assist_scope default: {cfg.assist_scope_default})")

    @app.cli.command("seed")
    def seed_command():
        """Load the full synthetic demo state through the real pipeline."""
        from seeds.seed import seed_all

        with open_db(cfg.database_path) as db:
            init_db(db, cfg.assist_scope_default)
            summary = seed_all(db, cfg)
        click.echo(summary)

    @app.cli.command("inject")
    @click.option("--scenario", required=True, help="Scenario name, e.g. mia_appointment_with_profile_change")
    @click.option("--external-id", default=None, help="Fix the external message id (replay/idempotency demos)")
    def inject_command(scenario: str, external_id: str | None):
        """Inject one synthetic inbound message through the real ingestion pipeline."""
        from .inbound.ingest import ingest_message
        from .inbound.scenarios import SCENARIOS, build_payload

        if scenario not in SCENARIOS:
            raise click.ClickException(f"Unknown scenario {scenario!r}. Known: {', '.join(sorted(SCENARIOS))}")
        with open_db(cfg.database_path) as db:
            result = ingest_message(db, cfg, build_payload(scenario, external_id=external_id))
        click.echo(result)

    return app
