#!/usr/bin/env python3
"""Fix Playwright browser path when Cursor Agent injects an empty sandbox cache.

Cursor may set PLAYWRIGHT_BROWSERS_PATH to
  %TEMP%/cursor-sandbox-cache/.../playwright
which often has no Chromium binaries. This module falls back to the normal
user install at %LOCALAPPDATA%/ms-playwright when the env path is unusable.
"""

from __future__ import annotations

import os
from pathlib import Path


def _has_chromium_binaries(root: Path) -> bool:
    if not root.is_dir():
        return False
    # Full Chromium or headless shell (Playwright 1.4x+)
    for pattern in (
        "chromium-*/chrome-win64/chrome.exe",
        "chromium-*/chrome-win/chrome.exe",
        "chromium_headless_shell-*/chrome-headless-shell-win64/chrome-headless-shell.exe",
        "chromium_headless_shell-*/chrome-headless-shell-win/chrome-headless-shell.exe",
    ):
        if any(root.glob(pattern)):
            return True
    # Last resort: any chrome*.exe under the tree (depth-limited via glob)
    return any(root.rglob("chrome*.exe"))


def ensure_playwright_browsers_path() -> str | None:
    """Ensure PLAYWRIGHT_BROWSERS_PATH points at a directory with Chromium.

    Returns the path that will be used (or None if env was cleared for default).
    """
    current = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    if current and _has_chromium_binaries(Path(current)):
        return current

    localappdata = os.environ.get("LOCALAPPDATA", "").strip()
    if localappdata:
        local = Path(localappdata) / "ms-playwright"
        if _has_chromium_binaries(local):
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(local)
            return str(local)

    # Drop broken sandbox path so Playwright can try its own default resolution
    if current:
        os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)
    return None
