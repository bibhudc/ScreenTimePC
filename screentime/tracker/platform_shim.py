"""
Platform abstraction for window tracking.
Windows: uses Win32 APIs for foreground window and idle detection.
macOS: stubs for development/testing.
"""

import sys
import os
from dataclasses import dataclass


@dataclass
class WindowInfo:
    pid: int
    title: str
    app_name: str


def _is_windows():
    return sys.platform == "win32"


if _is_windows():
    import ctypes
    from ctypes import Structure, c_uint, sizeof, byref
    import win32gui
    import win32process
    import psutil

    class LASTINPUTINFO(Structure):
        _fields_ = [("cbSize", c_uint), ("dwTime", c_uint)]

    def get_foreground_window_info() -> WindowInfo | None:
        """Get info about the current foreground window on Windows."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None

            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            try:
                process = psutil.Process(pid)
                app_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                app_name = "unknown"

            return WindowInfo(pid=pid, title=title, app_name=app_name)
        except Exception:
            return None

    def get_idle_seconds() -> float:
        """Get seconds since last user input (mouse/keyboard) on Windows."""
        info = LASTINPUTINFO()
        info.cbSize = sizeof(info)
        ctypes.windll.user32.GetLastInputInfo(byref(info))
        millis = ctypes.windll.kernel32.GetTickCount() - info.dwTime
        return millis / 1000.0

else:
    # macOS / Linux stubs for development
    import subprocess
    import random

    _STUB_APPS = [
        ("chrome.exe", "Google Docs - My Essay - Google Chrome"),
        ("chrome.exe", "YouTube - Funny Cat Videos - Google Chrome"),
        ("chrome.exe", "Reddit - r/gaming - Google Chrome"),
        ("chrome.exe", "Khan Academy - Algebra - Google Chrome"),
        ("steam.exe", "Steam"),
        ("discord.exe", "Discord"),
        ("minecraft.exe", "Minecraft 1.20.4"),
        ("explorer.exe", "File Explorer"),
        ("code.exe", "Visual Studio Code"),
        ("chrome.exe", "Netflix - Google Chrome"),
        ("chrome.exe", "Instagram - Google Chrome"),
        ("msedge.exe", "Google Classroom - Microsoft Edge"),
    ]

    def get_foreground_window_info() -> WindowInfo | None:
        """macOS stub: returns simulated window info for development."""
        if os.environ.get("SCREENTIME_DEV_SIMULATE"):
            app_name, title = random.choice(_STUB_APPS)
            return WindowInfo(pid=random.randint(1000, 9999), title=title, app_name=app_name)

        # Try to get actual foreground app on macOS via osascript
        try:
            result = subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to get name of first application process whose frontmost is true'],
                capture_output=True, text=True, timeout=2
            )
            app_name = result.stdout.strip() if result.returncode == 0 else "unknown"

            result2 = subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to get title of front window of first application process whose frontmost is true'],
                capture_output=True, text=True, timeout=2
            )
            title = result2.stdout.strip() if result2.returncode == 0 else ""

            return WindowInfo(pid=0, title=title, app_name=app_name)
        except Exception:
            return WindowInfo(pid=0, title="Development Mode", app_name="dev_stub")

    def get_idle_seconds() -> float:
        """macOS stub: always returns 0 (active)."""
        return 0.0
