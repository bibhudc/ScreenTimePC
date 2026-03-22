#!/usr/bin/env python3
"""
Uninstall ScreenTimePC service and watchdog scheduled task.
Must be run as Administrator.
"""

import sys
import os
import subprocess
from pathlib import Path

if sys.platform != "win32":
    print("This script only runs on Windows.")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVICE_SCRIPT = PROJECT_ROOT / "screentime" / "service" / "win_service.py"
APP_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "ScreenTimePC"


def check_admin():
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("ERROR: This script must be run as Administrator.")
        sys.exit(1)


def main():
    print("=" * 50)
    print("  ScreenTimePC Uninstaller")
    print("=" * 50)
    print()

    check_admin()

    print("[1/3] Stopping service...")
    subprocess.run(
        [sys.executable, str(SERVICE_SCRIPT), "stop"],
        capture_output=True, text=True,
    )
    print("  Done")
    print()

    print("[2/3] Removing service...")
    result = subprocess.run(
        [sys.executable, str(SERVICE_SCRIPT), "remove"],
        capture_output=True, text=True,
    )
    print(result.stdout)
    print()

    print("[3/3] Removing watchdog scheduled task...")
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", "ScreenTimePC_Watchdog", "/f"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  Watchdog task removed")
    else:
        print(f"  Note: {result.stderr.strip()}")
    print()

    print("=" * 50)
    print("  Uninstall complete.")
    print()
    print("  Data and config have been preserved at:")
    print(f"    {APP_DIR}")
    print()
    print("  To remove all data, manually delete that folder.")
    print("=" * 50)


if __name__ == "__main__":
    main()
