"""
SQLite database schema and initialization.
"""

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS activity_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    app_name TEXT NOT NULL,
    window_title TEXT,
    category TEXT NOT NULL DEFAULT 'Other',
    is_idle INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_activity_start ON activity_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_activity_category ON activity_sessions(category);
CREATE INDEX IF NOT EXISTS idx_activity_app ON activity_sessions(app_name);
CREATE INDEX IF NOT EXISTS idx_activity_end ON activity_sessions(end_time);
"""


def init_db(db_path: str | Path) -> sqlite3.Connection:
    """Initialize the database: create tables if needed, enable WAL mode."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn
