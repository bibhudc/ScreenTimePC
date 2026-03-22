#!/usr/bin/env python3
"""
Development runner: starts the tracker and dashboard without a Windows service.
Works on macOS with stubs and on Windows natively.

Usage:
    python scripts/run_dev.py
    SCREENTIME_DEV_SIMULATE=1 python scripts/run_dev.py   # random simulated data
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

# Configuration
CONFIG_DIR = PROJECT_ROOT / "config"
CATEGORIES_PATH = CONFIG_DIR / "categories.json"
DB_PATH = PROJECT_ROOT / "data" / "screentime_dev.db"


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("run_dev")

    logger.info("Starting ScreenTimePC in development mode...")
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Categories config: {CATEGORIES_PATH}")

    if os.environ.get("SCREENTIME_DEV_SIMULATE"):
        logger.info("Simulation mode ON: generating random window data")

    # Initialize components
    conn = init_db(DB_PATH)
    repo = Repository(conn)
    categorizer = Categorizer(CATEGORIES_PATH)
    tracker = WindowTracker(repo, categorizer, poll_interval=5, idle_threshold=120)

    # Start tracker in a background thread
    tracker_thread = threading.Thread(target=tracker.run, daemon=True)
    tracker_thread.start()
    logger.info("Tracker thread started")

    # Handle Ctrl+C
    def shutdown(sig, frame):
        logger.info("Shutting down...")
        tracker.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Start dashboard (blocks)
    app = create_app(repo)
    logger.info("Dashboard: http://localhost:5123")
    app.run(host="127.0.0.1", port=5123, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
