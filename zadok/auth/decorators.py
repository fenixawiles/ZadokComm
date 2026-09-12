from __future__ import annotations

from functools import wraps

from flask import g, jsonify, redirect, request, session, url_for

from ..db import get_db
from ..repos import advisors as advisors_repo


def current_advisor():
    if "advisor" not in g:
        advisor_id = session.get("advisor_id")
        g.advisor = advisors_repo.by_id(get_db(), advisor_id) if advisor_id else None
    return g.advisor


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_advisor() is None:
            if request.path.startswith("/api/"):
                return jsonify({"error": "authentication required"}), 401
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped
