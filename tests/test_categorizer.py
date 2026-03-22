"""Tests for the categorization engine."""

import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from screentime.categorizer.engine import Categorizer


def _create_test_config():
    """Create a temporary categories config for testing."""
    config = {
        "categories": ["Gaming", "Homework/School", "Social Media", "Video/Streaming", "Productivity", "Other"],
        "rules": {
            "app_rules": [
                {"pattern": "steam.exe", "category": "Gaming"},
                {"pattern": "minecraft*", "category": "Gaming"},
                {"pattern": "discord.exe", "category": "Social Media"},
                {"pattern": "code.exe", "category": "Productivity"},
            ],
            "title_rules": [
                {"pattern": "*youtube*", "category": "Video/Streaming"},
                {"pattern": "*google docs*", "category": "Homework/School"},
                {"pattern": "*khan academy*", "category": "Homework/School"},
                {"pattern": "*reddit*", "category": "Social Media"},
                {"pattern": "*netflix*", "category": "Video/Streaming"},
            ]
        },
        "user_overrides": {}
    }
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(config, f)
    f.close()
    return f.name


def test_app_rules():
    path = _create_test_config()
    cat = Categorizer(path)
    assert cat.categorize("steam.exe", "Steam") == "Gaming"
    assert cat.categorize("discord.exe", "Discord") == "Social Media"
    assert cat.categorize("code.exe", "Visual Studio Code") == "Productivity"
    os.unlink(path)


def test_app_rules_wildcard():
    path = _create_test_config()
    cat = Categorizer(path)
    assert cat.categorize("minecraft.exe", "Minecraft 1.20") == "Gaming"
    assert cat.categorize("minecraftlauncher.exe", "Launcher") == "Gaming"
    os.unlink(path)


def test_title_rules():
    path = _create_test_config()
    cat = Categorizer(path)
    assert cat.categorize("chrome.exe", "Funny Video - YouTube - Google Chrome") == "Video/Streaming"
    assert cat.categorize("chrome.exe", "My Essay - Google Docs - Google Chrome") == "Homework/School"
    assert cat.categorize("msedge.exe", "r/gaming - Reddit - Microsoft Edge") == "Social Media"
    os.unlink(path)


def test_case_insensitive():
    path = _create_test_config()
    cat = Categorizer(path)
    assert cat.categorize("chrome.exe", "YOUTUBE - My Video") == "Video/Streaming"
    assert cat.categorize("STEAM.EXE", "Steam Client") == "Gaming"
    os.unlink(path)


def test_default_other():
    path = _create_test_config()
    cat = Categorizer(path)
    assert cat.categorize("unknown_app.exe", "Some Random Window") == "Other"
    os.unlink(path)


def test_user_overrides():
    path = _create_test_config()
    cat = Categorizer(path)

    # Add an override
    cat.add_override("roblox.exe", "Gaming")
    assert cat.categorize("roblox.exe", "Roblox") == "Gaming"

    # Override takes precedence
    cat.add_override("steam.exe", "Productivity")
    assert cat.categorize("steam.exe", "Steam") == "Productivity"
    os.unlink(path)


def test_categories_list():
    path = _create_test_config()
    cat = Categorizer(path)
    cats = cat.categories
    assert "Gaming" in cats
    assert "Homework/School" in cats
    os.unlink(path)


if __name__ == "__main__":
    test_app_rules()
    test_app_rules_wildcard()
    test_title_rules()
    test_case_insensitive()
    test_default_other()
    test_user_overrides()
    test_categories_list()
    print("All categorizer tests passed!")
