from __future__ import annotations

from pathlib import Path
from playwright.sync_api import sync_playwright
from service_osint.utils import APP_OUT, sha256_file, slugify, utc_stamp


def screenshot_url(url: str, label: str, full_page: bool = True, wait_ms: int = 1500) -> tuple[Path, str]:
    """Capture a public webpage screenshot. Does not bypass auth/paywalls/CAPTCHAs."""
    out_dir = APP_OUT / slugify(label)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{utc_stamp()}-{slugify(label)}.png"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
        page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        page.wait_for_timeout(wait_ms)
        page.screenshot(path=str(out), full_page=full_page)
        browser.close()
    return out, sha256_file(out)
