"""
Categorization engine: maps app names and window titles to activity categories.

Priority order:
1. User overrides (exact match on app_name or title substring)
2. App rules (fnmatch pattern on app_name)
3. Title rules (fnmatch pattern on window_title, case-insensitive)
4. Default: "Other"
"""

import json
import os
import time
from fnmatch import fnmatch
from pathlib import Path


DEFAULT_CATEGORY = "Other"
CONFIG_RELOAD_INTERVAL = 60  # seconds


class Categorizer:
    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self._config = {}
        self._last_load_time = 0.0
        self._load_config()

    def _load_config(self):
        """Load or reload the categories config file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            self._last_load_time = time.time()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load categories config: {e}")
            if not self._config:
                self._config = {"rules": {"app_rules": [], "title_rules": []}, "user_overrides": {}}

    def _maybe_reload(self):
        """Reload config if enough time has passed."""
        if time.time() - self._last_load_time > CONFIG_RELOAD_INTERVAL:
            self._load_config()

    def categorize(self, app_name: str, window_title: str) -> str:
        """
        Determine the category for a given app and window title.

        Returns the category string (e.g., "Gaming", "Homework/School").
        """
        self._maybe_reload()

        app_lower = app_name.lower()
        title_lower = window_title.lower()

        # 1. Check user overrides
        overrides = self._config.get("user_overrides", {})
        for key, category in overrides.items():
            if key.lower() == app_lower or key.lower() in title_lower:
                return category

        # 2. Check app rules
        app_rules = self._config.get("rules", {}).get("app_rules", [])
        for rule in app_rules:
            if fnmatch(app_lower, rule["pattern"].lower()):
                return rule["category"]

        # 3. Check title rules
        title_rules = self._config.get("rules", {}).get("title_rules", [])
        for rule in title_rules:
            if fnmatch(title_lower, rule["pattern"].lower()):
                return rule["category"]

        return DEFAULT_CATEGORY

    @property
    def categories(self) -> list[str]:
        """Return the list of defined categories."""
        self._maybe_reload()
        return self._config.get("categories", [DEFAULT_CATEGORY])

    def add_override(self, key: str, category: str):
        """Add a user override and persist to config file."""
        if "user_overrides" not in self._config:
            self._config["user_overrides"] = {}
        self._config["user_overrides"][key] = category
        self._save_config()

    def _save_config(self):
        """Write current config back to disk."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"Warning: Could not save categories config: {e}")
