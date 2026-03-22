"""Tests for browser title parser."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from screentime.tracker.browser_parser import parse_browser_title, is_browser


def test_chrome_title():
    result = parse_browser_title("YouTube - Funny Cats - Google Chrome", "chrome.exe")
    assert result.is_browser is True
    assert result.page_title == "YouTube - Funny Cats"
    assert result.browser_name == "Chrome"


def test_edge_title():
    result = parse_browser_title("Google Classroom - Microsoft Edge", "msedge.exe")
    assert result.is_browser is True
    assert result.page_title == "Google Classroom"


def test_firefox_title():
    result = parse_browser_title("Wikipedia - Mozilla Firefox", "firefox.exe")
    assert result.is_browser is True
    assert result.page_title == "Wikipedia"


def test_non_browser():
    result = parse_browser_title("Untitled - Notepad", "notepad.exe")
    assert result.is_browser is False
    assert result.page_title == "Untitled - Notepad"


def test_new_tab():
    result = parse_browser_title("New Tab - Google Chrome", "chrome.exe")
    assert result.is_browser is True
    assert result.page_title == "New Tab"


def test_is_browser():
    assert is_browser("chrome.exe") is True
    assert is_browser("Chrome.exe") is True
    assert is_browser("msedge.exe") is True
    assert is_browser("notepad.exe") is False
    assert is_browser("steam.exe") is False


def test_complex_title():
    result = parse_browser_title(
        "My Essay - Google Docs - Google Chrome", "chrome.exe"
    )
    assert result.is_browser is True
    assert result.page_title == "My Essay - Google Docs"


if __name__ == "__main__":
    test_chrome_title()
    test_edge_title()
    test_firefox_title()
    test_non_browser()
    test_new_tab()
    test_is_browser()
    test_complex_title()
    print("All browser parser tests passed!")
