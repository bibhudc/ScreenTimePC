"""
Extract page title from browser window titles.

Browsers display titles in predictable formats:
  Chrome:  "Page Title - Google Chrome"
  Edge:    "Page Title - Microsoft\u200b Edge"  (may have zero-width space)
  Firefox: "Page Title - Mozilla Firefox" or "Page Title \u2014 Mozilla Firefox"
  Brave:   "Page Title - Brave"
  Opera:   "Page Title - Opera"
"""

from dataclasses import dataclass

# Map executable names to their window title suffixes
BROWSER_SUFFIXES = {
    "chrome.exe": ["- Google Chrome"],
    "msedge.exe": ["- Microsoft\u200b Edge", "- Microsoft Edge"],
    "firefox.exe": ["- Mozilla Firefox", "\u2014 Mozilla Firefox"],
    "brave.exe": ["- Brave"],
    "opera.exe": ["- Opera"],
    "vivaldi.exe": ["- Vivaldi"],
}

# All known browser executable names
BROWSER_NAMES = set(BROWSER_SUFFIXES.keys())


@dataclass
class BrowserInfo:
    is_browser: bool
    browser_name: str
    page_title: str


def is_browser(app_name: str) -> bool:
    """Check if an app name is a known browser."""
    return app_name.lower() in BROWSER_NAMES


def parse_browser_title(window_title: str, app_name: str) -> BrowserInfo:
    """
    Parse a browser window title to extract the page title.

    Returns BrowserInfo with is_browser=False if the app is not a browser.
    """
    app_lower = app_name.lower()

    if app_lower not in BROWSER_NAMES:
        return BrowserInfo(is_browser=False, browser_name="", page_title=window_title)

    suffixes = BROWSER_SUFFIXES.get(app_lower, [])
    page_title = window_title

    for suffix in suffixes:
        # Find the last occurrence of the suffix
        idx = page_title.rfind(suffix)
        if idx > 0:
            page_title = page_title[:idx].rstrip(" -\u2014")
            break

    # Handle "New Tab" or empty titles
    if not page_title or page_title.lower() in ("new tab", "new page", "start page"):
        page_title = "New Tab"

    browser_name = app_lower.replace(".exe", "").capitalize()

    return BrowserInfo(
        is_browser=True,
        browser_name=browser_name,
        page_title=page_title,
    )
