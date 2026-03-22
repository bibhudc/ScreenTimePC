"""
Dashboard routes: page views and JSON API endpoints.
"""

from datetime import date, datetime
from pathlib import Path
from flask import Blueprint, render_template, jsonify, request, current_app

_dir = Path(__file__).resolve().parent
bp = Blueprint(
    "dashboard",
    __name__,
    static_folder=str(_dir / "static"),
    static_url_path="/static",
)


def _get_repo():
    return current_app.config["REPOSITORY"]


def _format_duration(seconds: int) -> str:
    """Format seconds into human-readable string."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


# ── Page Routes ───────────────────────────────────────────────

@bp.route("/")
def index():
    selected_date = request.args.get("date", date.today().isoformat())
    return render_template("index.html", selected_date=selected_date)


@bp.route("/details/<category>")
def details(category):
    selected_date = request.args.get("date", date.today().isoformat())
    return render_template("details.html", category=category, selected_date=selected_date)


# ── API Routes ────────────────────────────────────────────────

@bp.route("/api/summary")
def api_summary():
    """Category breakdown for pie chart."""
    d = request.args.get("date", date.today().isoformat())
    repo = _get_repo()
    summary = repo.get_summary_by_category(d)
    idle_active = repo.get_idle_vs_active(d)

    return jsonify({
        "date": d,
        "categories": summary,
        "idle_active": idle_active,
        "total_active": idle_active.get("active", 0),
        "total_idle": idle_active.get("idle", 0),
    })


@bp.route("/api/top-apps")
def api_top_apps():
    """Top applications by time."""
    d = request.args.get("date", date.today().isoformat())
    limit = request.args.get("limit", 10, type=int)
    repo = _get_repo()
    apps = repo.get_summary_by_app(d, limit=limit)
    return jsonify({"date": d, "apps": apps})


@bp.route("/api/top-websites")
def api_top_websites():
    """Top browser page titles by time."""
    d = request.args.get("date", date.today().isoformat())
    limit = request.args.get("limit", 10, type=int)
    repo = _get_repo()
    sites = repo.get_top_websites(d, limit=limit)
    return jsonify({"date": d, "websites": sites})


@bp.route("/api/timeline")
def api_timeline():
    """Activity timeline for a given date."""
    d = request.args.get("date", date.today().isoformat())
    repo = _get_repo()
    timeline = repo.get_timeline(d)
    return jsonify({"date": d, "timeline": timeline})


@bp.route("/api/trends")
def api_trends():
    """Daily totals by category for trend charts."""
    days = request.args.get("days", 30, type=int)
    repo = _get_repo()
    totals = repo.get_daily_totals(days)
    return jsonify({"days": days, "totals": totals})


@bp.route("/api/sessions")
def api_sessions():
    """Paginated session list with date range support."""
    today = date.today().isoformat()
    start_date = request.args.get("start_date", today)
    end_date = request.args.get("end_date", today)
    # Also support legacy "date" param (single day)
    if "date" in request.args and "start_date" not in request.args:
        start_date = request.args["date"]
        end_date = request.args["date"]
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    per_page = min(per_page, 200)  # cap at 200

    repo = _get_repo()
    result = repo.get_sessions_paginated(start_date, end_date, page, per_page)
    result["start_date"] = start_date
    result["end_date"] = end_date
    return jsonify(result)


@bp.route("/api/recategorize", methods=["POST"])
def api_recategorize():
    """Update a session's category."""
    data = request.get_json()
    if not data or "session_id" not in data or "category" not in data:
        return jsonify({"error": "Missing session_id or category"}), 400

    repo = _get_repo()
    repo.update_category(data["session_id"], data["category"])
    return jsonify({"ok": True})
