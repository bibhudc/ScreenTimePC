"""Tests for the database repository."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta
from screentime.db.models import init_db
from screentime.db.repository import Repository


def _create_test_repo():
    """Create an in-memory test database."""
    conn = init_db(":memory:")
    return Repository(conn)


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def _make_time(hour, minute=0):
    """Create an ISO timestamp for today at the given hour."""
    return datetime.now().replace(hour=hour, minute=minute, second=0).isoformat(timespec="seconds")


def test_insert_and_retrieve():
    repo = _create_test_repo()
    repo.insert_session(
        start_time=_make_time(10, 0),
        end_time=_make_time(10, 30),
        duration_seconds=1800,
        app_name="chrome.exe",
        window_title="YouTube - Google Chrome",
        category="Video/Streaming",
        is_idle=False,
    )

    sessions = repo.get_sessions_for_date(_today())
    assert len(sessions) == 1
    assert sessions[0]["app_name"] == "chrome.exe"
    assert sessions[0]["duration_seconds"] == 1800
    assert sessions[0]["category"] == "Video/Streaming"


def test_summary_by_category():
    repo = _create_test_repo()
    repo.insert_session(_make_time(10), _make_time(10, 30), 1800, "chrome.exe", "YouTube", "Video/Streaming", False)
    repo.insert_session(_make_time(11), _make_time(11, 45), 2700, "chrome.exe", "Google Docs", "Homework/School", False)
    repo.insert_session(_make_time(12), _make_time(12, 15), 900, "steam.exe", "Steam", "Gaming", False)

    summary = repo.get_summary_by_category(_today())
    assert summary["Homework/School"] == 2700
    assert summary["Video/Streaming"] == 1800
    assert summary["Gaming"] == 900


def test_idle_excluded_from_summary():
    repo = _create_test_repo()
    repo.insert_session(_make_time(10), _make_time(10, 30), 1800, "chrome.exe", "YouTube", "Video/Streaming", False)
    repo.insert_session(_make_time(10, 30), _make_time(11), 1800, "", "", "Idle", True)

    summary = repo.get_summary_by_category(_today())
    assert "Idle" not in summary
    assert summary.get("Video/Streaming") == 1800


def test_summary_by_app():
    repo = _create_test_repo()
    repo.insert_session(_make_time(10), _make_time(10, 30), 1800, "chrome.exe", "YouTube", "Video/Streaming", False)
    repo.insert_session(_make_time(11), _make_time(11, 30), 1800, "steam.exe", "Steam", "Gaming", False)
    repo.insert_session(_make_time(12), _make_time(13), 3600, "chrome.exe", "Google Docs", "Homework/School", False)

    apps = repo.get_summary_by_app(_today())
    assert len(apps) == 2
    assert apps[0]["app_name"] == "chrome.exe"
    assert apps[0]["total"] == 5400  # 1800 + 3600


def test_idle_vs_active():
    repo = _create_test_repo()
    repo.insert_session(_make_time(10), _make_time(10, 30), 1800, "chrome.exe", "Test", "Other", False)
    repo.insert_session(_make_time(10, 30), _make_time(11), 1800, "", "", "Idle", True)

    result = repo.get_idle_vs_active(_today())
    assert result["active"] == 1800
    assert result["idle"] == 1800


def test_update_category():
    repo = _create_test_repo()
    row_id = repo.insert_session(_make_time(10), _make_time(10, 30), 1800, "unknown.exe", "Test", "Other", False)

    repo.update_category(row_id, "Productivity")
    sessions = repo.get_sessions_for_date(_today())
    assert sessions[0]["category"] == "Productivity"


def test_timeline():
    repo = _create_test_repo()
    repo.insert_session(_make_time(9), _make_time(9, 30), 1800, "steam.exe", "Game", "Gaming", False)
    repo.insert_session(_make_time(10), _make_time(10, 30), 1800, "chrome.exe", "Docs", "Homework/School", False)

    timeline = repo.get_timeline(_today())
    assert len(timeline) == 2
    assert timeline[0]["category"] == "Gaming"
    assert timeline[1]["category"] == "Homework/School"


if __name__ == "__main__":
    test_insert_and_retrieve()
    test_summary_by_category()
    test_idle_excluded_from_summary()
    test_summary_by_app()
    test_idle_vs_active()
    test_update_category()
    test_timeline()
    print("All repository tests passed!")
