#!/usr/bin/env python3
"""
Uninstall ScreenTimePC: stop tracker, remove scheduled tasks, clean up.
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


def kill_tracker():
    """Kill any running tracker processes."""
    result = subprocess.run(
        ["taskkill", "/f", "/im", "pythonw.exe", "/fi", f"MODULES eq run_tracker*"],
        capture_output=True, text=True,
    )
    # Also try a broader approach: kill anything listening on port 5123
    subprocess.run(
        ["powershell", "-Command",
         "Get-NetTCPConnection -LocalPort 5123 -ErrorAction SilentlyContinue | "
         "ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"],
        capture_output=True,
    )


def main():
    print("=" * 50)
    print("  ScreenTimePC Uninstaller")
    print("=" * 50)
    print()

    check_admin()

    print("[1/4] Stopping tracker process...")
    kill_tracker()
    print("  Done")
    print()

    print("[2/4] Removing logon task...")
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", "ScreenTimePC", "/f"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  Logon task removed")
    else:
        print(f"  Note: {result.stderr.strip()}")
    print()

    print("[3/4] Removing watchdog scheduled task...")
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", "ScreenTimePC_Watchdog", "/f"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  Watchdog task removed")
    else:
        print(f"  Note: {result.stderr.strip()}")
    print()

    print("[4/4] Removing old Windows service (if any)...")
    subprocess.run(["sc", "stop", "ScreenTimePC"], capture_output=True)
    result = subprocess.run(
        ["sc", "delete", "ScreenTimePC"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  Old service removed")
    else:
        print("  No old service found (OK)")
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
