#!/usr/bin/env python3
"""
Production runner: starts the tracker and dashboard in the user's session.

Unlike a Windows service (which runs in Session 0 and CANNOT see the desktop),
this runs in the logged-in user's session and has full access to
GetForegroundWindow().

Designed to be launched at logon via Task Scheduler or Startup folder.

Usage:
    pythonw scripts/run_tracker.py          # hidden (no console window)
    python  scripts/run_tracker.py          # visible (for debugging)
"""

import os
import sys
import signal
import threading
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from screentime.db.models import init_db
from screentime.db.repository import Repository
from screentime.categorizer.engine import Categorizer
from screentime.tracker.window_tracker import WindowTracker
from screentime.dashboard.app import create_app


def _get_app_dir():
    """Get the app data directory."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        return Path(local_app_data) / "ScreenTimePC"
    return PROJECT_ROOT / "data"


def main():
    app_dir = _get_app_dir()
    app_dir.mkdir(parents=True, exist_ok=True)

    db_path = app_dir / "screentime.db"
    log_path = app_dir / "screentime.log"

    # Config: prefer installed copy, fall back to project root
    config_dir = app_dir / "config"
    if not config_dir.exists():
        config_dir = PROJECT_ROOT / "config"
    categories_path = config_dir / "categories.json"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path),
        ],
    )
    logger = logging.getLogger("screentime")

    logger.info("ScreenTimePC starting...")
    logger.info(f"Database: {db_path}")
    logger.info(f"Config: {config_dir}")
    logger.info(f"Log: {log_path}")

    try:
        # Initialize components
        conn = init_db(db_path)
        repo = Repository(conn)
        categorizer = Categorizer(categories_path)
        tracker = WindowTracker(repo, categorizer, poll_interval=5, idle_threshold=120)

        # Start tracker in a background thread
        tracker_thread = threading.Thread(target=tracker.run, daemon=True)
        tracker_thread.start()
        logger.info("Tracker started")

        # Handle shutdown signals
        def shutdown(sig, frame):
            logger.info("Shutting down...")
            tracker.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        # Start dashboard (blocks)
        app = create_app(repo)
        logger.info("Dashboard: http://localhost:5123")
        app.run(host="0.0.0.0", port=5123, debug=False, use_reloader=False)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
