"""Authenticated, idempotent inbound webhook."""
from __future__ import annotations

import hmac

from flask import Blueprint, current_app, jsonify, request

from ..db import get_db
from .ingest import InvalidPayload, ingest_message

bp = Blueprint("webhooks", __name__)


@bp.post("/webhooks/inbound")
def inbound_webhook():
    cfg = current_app.config["ZADOK"]
    token = request.headers.get("X-Zadok-Webhook-Token", "")
    if not (cfg.webhook_shared_secret and hmac.compare_digest(token, cfg.webhook_shared_secret)):
        return jsonify({"error": "invalid webhook token"}), 401

    payload = request.get_json(silent=True)
    db = get_db()
    try:
        result = ingest_message(db, cfg, payload)
    except InvalidPayload as exc:
        return jsonify({"error": "invalid payload", "problems": exc.problems}), 422
    db.commit()
    return jsonify(result), 200 if result["duplicate"] else 201
