"""
Database repository: CRUD operations for activity sessions.
"""

import sqlite3
import threading
from datetime import datetime


class Repository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._lock = threading.Lock()

    def insert_session(self, start_time: str, end_time: str, duration_seconds: int,
                       app_name: str, window_title: str, category: str, is_idle: bool) -> int:
        """Insert a completed activity session. Returns the row id."""
        with self._lock:
            cursor = self.conn.execute(
                """INSERT INTO activity_sessions
                   (start_time, end_time, duration_seconds, app_name, window_title, category, is_idle)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (start_time, end_time, duration_seconds, app_name, window_title, category, int(is_idle))
            )
            self.conn.commit()
            return cursor.lastrowid

    def get_sessions_for_date(self, date: str) -> list[dict]:
        """Get all sessions for a given date (YYYY-MM-DD)."""
        cursor = self.conn.execute(
            """SELECT * FROM activity_sessions
               WHERE date(start_time) = ?
               ORDER BY start_time""",
            (date,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_sessions_for_range(self, start: str, end: str) -> list[dict]:
        """Get sessions within a datetime range."""
        cursor = self.conn.execute(
            """SELECT * FROM activity_sessions
               WHERE start_time >= ? AND start_time <= ?
               ORDER BY start_time""",
            (start, end)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_summary_by_category(self, date: str) -> dict[str, int]:
        """Get total seconds per category for a given date."""
        cursor = self.conn.execute(
            """SELECT category, SUM(duration_seconds) as total
               FROM activity_sessions
               WHERE date(start_time) = ? AND is_idle = 0
               GROUP BY category
               ORDER BY total DESC""",
            (date,)
        )
        return {row["category"]: row["total"] for row in cursor.fetchall()}

    def get_summary_by_app(self, date: str, limit: int = 10) -> list[dict]:
        """Get top apps by time for a given date."""
        cursor = self.conn.execute(
            """SELECT app_name, category, SUM(duration_seconds) as total
               FROM activity_sessions
               WHERE date(start_time) = ? AND is_idle = 0
               GROUP BY app_name
               ORDER BY total DESC
               LIMIT ?""",
            (date, limit)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_timeline(self, date: str) -> list[dict]:
        """Get ordered activity records for timeline view."""
        cursor = self.conn.execute(
            """SELECT start_time, end_time, duration_seconds, app_name,
                      window_title, category, is_idle
               FROM activity_sessions
               WHERE date(start_time) = ?
               ORDER BY start_time""",
            (date,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_daily_totals(self, days: int = 30) -> list[dict]:
        """Get daily totals by category for the last N days."""
        cursor = self.conn.execute(
            """SELECT date(start_time) as date, category,
                      SUM(duration_seconds) as total
               FROM activity_sessions
               WHERE date(start_time) >= date('now', ? || ' days') AND is_idle = 0
               GROUP BY date(start_time), category
               ORDER BY date(start_time)""",
            (f"-{days}",)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_idle_vs_active(self, date: str) -> dict[str, int]:
        """Get total idle and active seconds for a given date."""
        cursor = self.conn.execute(
            """SELECT is_idle, SUM(duration_seconds) as total
               FROM activity_sessions
               WHERE date(start_time) = ?
               GROUP BY is_idle""",
            (date,)
        )
        result = {"active": 0, "idle": 0}
        for row in cursor.fetchall():
            if row["is_idle"]:
                result["idle"] = row["total"]
            else:
                result["active"] = row["total"]
        return result

    def update_category(self, session_id: int, new_category: str):
        """Update the category of a session (for recategorization)."""
        with self._lock:
            self.conn.execute(
                "UPDATE activity_sessions SET category = ? WHERE id = ?",
                (new_category, session_id)
            )
            self.conn.commit()

    def get_sessions_paginated(self, start_date: str, end_date: str,
                                page: int = 1, per_page: int = 50) -> dict:
        """Get paginated sessions within a date range. Returns {sessions, total, page, per_page, pages}."""
        offset = (page - 1) * per_page

        # Get total count
        count_cursor = self.conn.execute(
            """SELECT COUNT(*) as cnt FROM activity_sessions
               WHERE date(start_time) >= ? AND date(start_time) <= ? AND is_idle = 0""",
            (start_date, end_date)
        )
        total = count_cursor.fetchone()["cnt"]

        # Get page of results
        cursor = self.conn.execute(
            """SELECT * FROM activity_sessions
               WHERE date(start_time) >= ? AND date(start_time) <= ? AND is_idle = 0
               ORDER BY start_time DESC
               LIMIT ? OFFSET ?""",
            (start_date, end_date, per_page, offset)
        )
        sessions = [dict(row) for row in cursor.fetchall()]

        import math
        return {
            "sessions": sessions,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": math.ceil(total / per_page) if total > 0 else 1,
        }

    def get_top_websites(self, date: str, limit: int = 10) -> list[dict]:
        """Get top browser window titles (websites) by time."""
        browser_apps = ("chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "vivaldi.exe")
        placeholders = ",".join("?" for _ in browser_apps)
        cursor = self.conn.execute(
            f"""SELECT window_title, category, SUM(duration_seconds) as total
                FROM activity_sessions
                WHERE date(start_time) = ? AND is_idle = 0
                  AND LOWER(app_name) IN ({placeholders})
                GROUP BY window_title
                ORDER BY total DESC
                LIMIT ?""",
            (date, *browser_apps, limit)
        )
        return [dict(row) for row in cursor.fetchall()]
