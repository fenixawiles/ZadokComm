"""Development-only message simulator (404 in production)."""
from __future__ import annotations

from flask import Blueprint, abort, current_app, jsonify, render_template, request

from ..db import get_db
from .ingest import InvalidPayload, ingest_message
from .scenarios import SCENARIOS, build_payload

bp = Blueprint("devtools", __name__)


@bp.before_request
def _dev_only():
    if current_app.config["ZADOK"].is_production:
        abort(404)


@bp.get("/dev/simulator")
def simulator():
    return render_template("simulator.html", scenarios=SCENARIOS)


@bp.post("/dev/simulator/inject")
def inject():
    cfg = current_app.config["ZADOK"]
    data = request.get_json(silent=True) or request.form.to_dict()
    db = get_db()
    try:
        if data.get("scenario"):
            payload = build_payload(data["scenario"])
        else:
            payload = {
                "source": "simulator",
                "external_message_id": data.get("external_message_id") or None,
                "from": {"email": data.get("from_email", ""), "name": data.get("from_name", "")},
                "subject": data.get("subject", ""),
                "body": data.get("body", ""),
            }
            if not payload["external_message_id"]:
                import uuid

                payload["external_message_id"] = f"freeform-{uuid.uuid4().hex[:10]}"
        result = ingest_message(db, cfg, payload)
    except KeyError:
        return jsonify({"error": f"unknown scenario {data.get('scenario')!r}"}), 422
    except InvalidPayload as exc:
        return jsonify({"error": "invalid payload", "problems": exc.problems}), 422
    db.commit()
    return jsonify(result), 200 if result["duplicate"] else 201
