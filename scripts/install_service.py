#!/usr/bin/env python3
"""
Install ScreenTimePC as a logon task with a watchdog scheduled task.
Must be run as Administrator.

Why not a Windows service? Services run in Session 0, which is isolated
from the interactive desktop on Windows 10/11. GetForegroundWindow()
returns nothing there. Instead, we use a scheduled task that runs at
user logon — same session, full desktop access, survives reboots.
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
TRACKER_SCRIPT = PROJECT_ROOT / "scripts" / "run_tracker.py"
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


def remove_old_service():
    """Remove the old Windows service if it exists (from previous installs)."""
    result = subprocess.run(
        ["sc", "query", "ScreenTimePC"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  Found old Windows service, removing...")
        subprocess.run(["sc", "stop", "ScreenTimePC"], capture_output=True)
        subprocess.run(["sc", "delete", "ScreenTimePC"], capture_output=True)
        print("  Old service removed")


def install_logon_task():
    """Create a scheduled task that runs at user logon.

    Uses pythonw.exe (no console window) to run the tracker hidden.
    The task runs in the user's interactive session, so it can see
    the desktop and track foreground windows.
    """
    # Use pythonw.exe for hidden execution (no console window)
    python_dir = Path(sys.executable).parent
    pythonw = python_dir / "pythonw.exe"
    if not pythonw.exists():
        pythonw = Path(sys.executable)  # fallback to python.exe
        print(f"  Note: pythonw.exe not found, using python.exe (console window will be visible)")

    username = os.environ.get("USERNAME", "")
    userdomain = os.environ.get("USERDOMAIN", ".")
    full_user = f"{userdomain}\\{username}"

    # Remove existing task if present
    subprocess.run(
        ["schtasks", "/delete", "/tn", "ScreenTimePC", "/f"],
        capture_output=True,
    )

    result = subprocess.run([
        "schtasks", "/create",
        "/tn", "ScreenTimePC",
        "/tr", f'"{pythonw}" "{TRACKER_SCRIPT}"',
        "/sc", "onlogon",
        "/ru", full_user,
        "/rl", "highest",
        "/f",
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"  Logon task created for user: {full_user}")
        print(f"  Using: {pythonw}")
        return True
    else:
        print(f"  Error creating logon task: {result.stderr}")
        return False


def start_tracker_now():
    """Start the tracker immediately (don't wait for next logon)."""
    python_dir = Path(sys.executable).parent
    pythonw = python_dir / "pythonw.exe"
    if not pythonw.exists():
        pythonw = Path(sys.executable)

    subprocess.Popen(
        [str(pythonw), str(TRACKER_SCRIPT)],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
    )
    print("  Tracker started in background")


def install_watchdog():
    """Create a scheduled task that checks the tracker every 5 minutes."""
    python_exe = sys.executable
    # The watchdog checks if the tracker is running and restarts it if not
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


def add_firewall_rule():
    """Add a Windows Firewall rule to allow remote dashboard access on port 5123.

    Without this, the dashboard is only reachable from localhost.
    The Windows firewall prompt is unreliable, so we add it explicitly.
    """
    # Remove old rule if present (idempotent)
    subprocess.run(
        ["netsh", "advfirewall", "firewall", "delete", "rule",
         "name=ScreenTimePC Dashboard"],
        capture_output=True,
    )

    result = subprocess.run(
        ["netsh", "advfirewall", "firewall", "add", "rule",
         "name=ScreenTimePC Dashboard",
         "dir=in", "action=allow", "protocol=tcp", "localport=5123"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  Firewall rule added (TCP port 5123 open for remote access)")
    else:
        print(f"  Warning: Could not add firewall rule: {result.stderr}")
        print("  You may need to manually allow port 5123 in Windows Firewall")


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

    print("[1/6] Setting up configuration...")
    setup_config()
    print()

    print("[2/6] Removing old service (if any)...")
    remove_old_service()
    print()

    print("[3/6] Creating logon task...")
    if not install_logon_task():
        print("  Failed to create logon task. Aborting.")
        sys.exit(1)
    print()

    print("[4/6] Starting tracker now...")
    start_tracker_now()
    print()

    print("[5/6] Installing watchdog scheduled task...")
    install_watchdog()
    print()

    print("[6/6] Adding firewall rule for remote access...")
    add_firewall_rule()
    print()

    ip = get_local_ip()
    print("=" * 50)
    print("  Installation complete!")
    print()
    print(f"  Dashboard: http://{ip}:5123")
    print(f"  Also at:   http://localhost:5123")
    print(f"  Config:    {CONFIG_DIR}")
    print(f"  Database:  {APP_DIR / 'screentime.db'}")
    print(f"  Logs:      {APP_DIR / 'screentime.log'}")
    print()
    print("  The tracker is running now and will auto-start on logon.")
    print("  To customize categories, edit:")
    print(f"    {CONFIG_DIR / 'categories.json'}")
    print("=" * 50)


if __name__ == "__main__":
    main()
