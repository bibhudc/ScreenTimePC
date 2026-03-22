#!/usr/bin/env python3
"""
Install ScreenTimePC as a Windows service with a watchdog scheduled task.
Must be run as Administrator.
"""

import sys
import os
import shutil
import subprocess
import socket
from pathlib import Path

if sys.platform != "win32":
    print("This installer only runs on Windows.")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "ScreenTimePC"
CONFIG_DIR = APP_DIR / "config"
SERVICE_SCRIPT = PROJECT_ROOT / "screentime" / "service" / "win_service.py"
WATCHDOG_SCRIPT = PROJECT_ROOT / "screentime" / "service" / "watchdog.py"


def check_admin():
    """Check if running with admin privileges."""
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("ERROR: This script must be run as Administrator.")
        print("Right-click Command Prompt -> Run as Administrator")
        sys.exit(1)


def setup_config():
    """Copy default config files to app directory."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    source_config = PROJECT_ROOT / "config"

    for config_file in source_config.glob("*.json"):
        dest = CONFIG_DIR / config_file.name
        if not dest.exists():
            shutil.copy2(config_file, dest)
            print(f"  Copied {config_file.name} -> {dest}")
        else:
            print(f"  {config_file.name} already exists, skipping")


def install_service():
    """Install the Windows service."""
    python_exe = sys.executable
    print(f"  Using Python: {python_exe}")

    result = subprocess.run(
        [python_exe, str(SERVICE_SCRIPT), "install"],
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"  Error: {result.stderr}")
        return False

    # Set to auto-start
    subprocess.run(
        ["sc", "config", "ScreenTimePC", "start=", "auto"],
        capture_output=True,
    )
    print("  Service set to auto-start")
    return True


def start_service():
    """Start the service."""
    result = subprocess.run(
        [sys.executable, str(SERVICE_SCRIPT), "start"],
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"  Warning: {result.stderr}")


def install_watchdog():
    """Create a scheduled task for the watchdog."""
    python_exe = sys.executable
    task_cmd = f'"{python_exe}" "{WATCHDOG_SCRIPT}"'

    result = subprocess.run([
        "schtasks", "/create",
        "/tn", "ScreenTimePC_Watchdog",
        "/tr", task_cmd,
        "/sc", "minute",
        "/mo", "5",
        "/ru", "SYSTEM",
        "/f",
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("  Watchdog scheduled task created (runs every 5 minutes)")
    else:
        print(f"  Warning: Could not create watchdog task: {result.stderr}")


def get_local_ip():
    """Get the machine's LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def main():
    print("=" * 50)
    print("  ScreenTimePC Installer")
    print("=" * 50)
    print()

    check_admin()

    print("[1/4] Setting up configuration...")
    setup_config()
    print()

    print("[2/4] Installing Windows service...")
    if not install_service():
        print("  Failed to install service. Aborting.")
        sys.exit(1)
    print()

    print("[3/4] Starting service...")
    start_service()
    print()

    print("[4/4] Installing watchdog scheduled task...")
    install_watchdog()
    print()

    ip = get_local_ip()
    print("=" * 50)
    print("  Installation complete!")
    print()
    print(f"  Dashboard: http://{ip}:5123")
    print(f"  Config:    {CONFIG_DIR}")
    print(f"  Database:  {APP_DIR / 'screentime.db'}")
    print()
    print("  To customize categories, edit:")
    print(f"    {CONFIG_DIR / 'categories.json'}")
    print("=" * 50)


if __name__ == "__main__":
    main()
