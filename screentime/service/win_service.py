"""
Windows service wrapper for ScreenTimePC.

Runs the window tracker and Flask dashboard as a Windows service.
Install/manage via:
    python win_service.py install
    python win_service.py start
    python win_service.py stop
    python win_service.py remove
"""

import sys
import os
import threading
import logging
from pathlib import Path

# Only import win32 modules on Windows
if sys.platform == "win32":
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _get_config_dir():
    """Get config directory: prefer LOCALAPPDATA, fall back to project root."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    app_dir = Path(local_app_data) / "ScreenTimePC" if local_app_data else PROJECT_ROOT
    config_dir = app_dir / "config"
    if config_dir.exists():
        return config_dir
    return PROJECT_ROOT / "config"


def _get_db_path():
    """Get database path."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        return Path(local_app_data) / "ScreenTimePC" / "screentime.db"
    return PROJECT_ROOT / "data" / "screentime.db"


def _setup_logging():
    log_dir = _get_db_path().parent
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "screentime.log"),
        ],
    )


if sys.platform == "win32":
    class ScreenTimeService(win32serviceutil.ServiceFramework):
        _svc_name_ = "ScreenTimePC"
        _svc_display_name_ = "ScreenTimePC Activity Monitor"
        _svc_description_ = (
            "Monitors foreground window activity and serves a screen time dashboard. "
            "Dashboard available at http://localhost:5123"
        )

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.is_running = True

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.stop_event)
            self.is_running = False

        def SvcDoRun(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )
            self.main()

        def main(self):
            _setup_logging()
            logger = logging.getLogger("service")

            try:
                from screentime.db.models import init_db
                from screentime.db.repository import Repository
                from screentime.categorizer.engine import Categorizer
                from screentime.tracker.window_tracker import WindowTracker
                from screentime.dashboard.app import create_app

                config_dir = _get_config_dir()
                db_path = _get_db_path()

                logger.info(f"Config dir: {config_dir}")
                logger.info(f"Database: {db_path}")

                # Initialize
                conn = init_db(db_path)
                repo = Repository(conn)
                categorizer = Categorizer(config_dir / "categories.json")
                tracker = WindowTracker(repo, categorizer, poll_interval=5, idle_threshold=120)

                # Start dashboard in a daemon thread
                app = create_app(repo)
                dashboard_thread = threading.Thread(
                    target=lambda: app.run(host="0.0.0.0", port=5123, debug=False, use_reloader=False),
                    daemon=True,
                )
                dashboard_thread.start()
                logger.info("Dashboard started on port 5123")

                # Run tracker in main thread (checks self.is_running)
                logger.info("Tracker started")
                while self.is_running:
                    try:
                        tracker.poll_once()
                    except Exception as e:
                        logger.error(f"Poll error: {e}")

                    # Wait for poll interval or stop event
                    result = win32event.WaitForSingleObject(self.stop_event, 5000)
                    if result == win32event.WAIT_OBJECT_0:
                        break

                # Finalize
                tracker.stop()
                logger.info("Service stopped")

            except Exception as e:
                logger.error(f"Service error: {e}", exc_info=True)
                raise


if __name__ == "__main__":
    if sys.platform != "win32":
        print("This service can only run on Windows.")
        print("Use 'python scripts/run_dev.py' for development.")
        sys.exit(1)

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ScreenTimeService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ScreenTimeService)
