"""Pick-a-rep login with a shared dev passcode.

This is a development shell, not authentication — config.py refuses to boot
in production while this is the auth story. Real deployment: SSO.
"""
from __future__ import annotations

import hmac

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

from .. import audit
from ..db import get_db
from ..repos import advisors as advisors_repo

bp = Blueprint("auth", __name__)


@bp.get("/login")
def login():
    db = get_db()
    return render_template("login.html", advisors=advisors_repo.all_active(db),
                           error=request.args.get("error"))


@bp.post("/login")
def login_submit():
    cfg = current_app.config["ZADOK"]
    slug = request.form.get("advisor_slug", "")
    passcode = request.form.get("passcode", "")
    db = get_db()
    advisor = advisors_repo.by_slug(db, slug)
    if advisor is None or not hmac.compare_digest(passcode, cfg.dev_passcode):
        return redirect(url_for("auth.login", error="Unknown advisor or wrong passcode."))
    session.clear()
    session["advisor_id"] = advisor["id"]
    audit.record(db, "advisor_login", actor_type="advisor", actor_id=advisor["id"])
    db.commit()
    return redirect(url_for("review.inbox"))


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
