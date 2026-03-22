"""
Main window tracking loop.

Polls the foreground window at regular intervals and logs activity sessions
to the database. Uses a session model: accumulates time while the same window
is active, writes to DB when the window changes.
"""

import time
import logging
from datetime import datetime, timezone

from screentime.tracker.platform_shim import get_foreground_window_info, get_idle_seconds
from screentime.tracker.browser_parser import parse_browser_title
from screentime.categorizer.engine import Categorizer
from screentime.db.repository import Repository

logger = logging.getLogger(__name__)


class WindowTracker:
    def __init__(self, repository: Repository, categorizer: Categorizer,
                 poll_interval: int = 5, idle_threshold: int = 120):
        self.repo = repository
        self.categorizer = categorizer
        self.poll_interval = poll_interval
        self.idle_threshold = idle_threshold
        self.is_running = False

        # Current session state
        self._current_app = None
        self._current_title = None
        self._current_category = None
        self._current_is_idle = False
        self._session_start = None

    def _now_iso(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _finalize_session(self):
        """Write the current session to the database."""
        if self._session_start is None or self._current_app is None:
            return

        end_time = self._now_iso()
        start_dt = datetime.fromisoformat(self._session_start)
        end_dt = datetime.fromisoformat(end_time)
        duration = int((end_dt - start_dt).total_seconds())

        if duration < 1:
            return

        try:
            self.repo.insert_session(
                start_time=self._session_start,
                end_time=end_time,
                duration_seconds=duration,
                app_name=self._current_app,
                window_title=self._current_title or "",
                category=self._current_category or "Other",
                is_idle=self._current_is_idle,
            )
        except Exception as e:
            logger.error(f"Failed to insert session: {e}")

    def _start_new_session(self, app_name: str, title: str, category: str, is_idle: bool):
        """Start tracking a new session."""
        self._current_app = app_name
        self._current_title = title
        self._current_category = category
        self._current_is_idle = is_idle
        self._session_start = self._now_iso()

    def poll_once(self):
        """Poll the foreground window and update session tracking."""
        info = get_foreground_window_info()
        if info is None:
            return

        idle_secs = get_idle_seconds()
        is_idle = idle_secs >= self.idle_threshold

        app_name = info.app_name
        title = info.title

        # For browsers, parse the page title for better categorization
        browser_info = parse_browser_title(title, app_name)
        if browser_info.is_browser:
            categorize_title = browser_info.page_title
        else:
            categorize_title = title

        category = "Idle" if is_idle else self.categorizer.categorize(app_name, categorize_title)

        # Check if the session has changed
        session_changed = (
            app_name != self._current_app
            or title != self._current_title
            or is_idle != self._current_is_idle
        )

        if session_changed:
            self._finalize_session()
            self._start_new_session(app_name, title, category, is_idle)

    def run(self):
        """Main tracking loop. Call stop() to exit."""
        self.is_running = True
        logger.info("Window tracker started (poll_interval=%ds, idle_threshold=%ds)",
                     self.poll_interval, self.idle_threshold)

        while self.is_running:
            try:
                self.poll_once()
            except Exception as e:
                logger.error(f"Error in poll cycle: {e}")

            time.sleep(self.poll_interval)

        # Finalize any in-progress session on shutdown
        self._finalize_session()
        logger.info("Window tracker stopped")

    def stop(self):
        """Signal the tracker to stop."""
        self.is_running = False
