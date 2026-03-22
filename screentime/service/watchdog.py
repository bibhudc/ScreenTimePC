"""
Watchdog script: checks if the ScreenTimePC service is running.
Designed to run as a Windows Scheduled Task every 5 minutes.

If the service is not running, logs a warning and attempts to restart it.
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _get_log_path():
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        log_dir = Path(local_app_data) / "ScreenTimePC"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "watchdog.log"
    return PROJECT_ROOT / "data" / "watchdog.log"


def check_service():
    """Check if the ScreenTimePC Windows service is running. Attempt restart if not."""
    if sys.platform != "win32":
        print("Watchdog only runs on Windows.")
        return

    import win32serviceutil
    import win32service
    import subprocess

    try:
        status = win32serviceutil.QueryServiceStatus("ScreenTimePC")
        state = status[1]

        if state == win32service.SERVICE_RUNNING:
            logging.info("Service is running normally.")
            return True
        else:
            state_names = {
                win32service.SERVICE_STOPPED: "STOPPED",
                win32service.SERVICE_START_PENDING: "START_PENDING",
                win32service.SERVICE_STOP_PENDING: "STOP_PENDING",
                win32service.SERVICE_PAUSED: "PAUSED",
            }
            state_name = state_names.get(state, f"UNKNOWN({state})")
            logging.warning(f"Service is NOT running! State: {state_name}")

            # Attempt to restart the service
            logging.info("Attempting to restart service...")
            try:
                subprocess.run(["sc", "start", "ScreenTimePC"], capture_output=True)
                logging.info("Restart command issued.")
            except Exception as e:
                logging.error(f"Failed to restart: {e}")

            return False

    except Exception as e:
        logging.error(f"Cannot query service: {e}")
        return False


if __name__ == "__main__":
    log_path = _get_log_path()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
    )
    check_service()
