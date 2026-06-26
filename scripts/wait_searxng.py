"""Wait for SearXNG to accept connections, then optionally run osint doctor."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        for path in (ROOT / ".env", Path.cwd() / ".env"):
            if path.is_file():
                load_dotenv(path, override=False)
                return
    except ImportError:
        return


def wait_searxng(*, timeout: float = 90.0, interval: float = 3.0) -> bool:
    _load_env()
    base = (os.getenv("SEARXNG_URL") or "").rstrip("/")
    if not base:
        print("SEARXNG_URL not set — skipping wait")
        return False

    deadline = time.monotonic() + timeout
    url = f"{base}/healthz"
    print(f"Waiting for SearXNG at {url} (up to {int(timeout)}s)...")
    while time.monotonic() < deadline:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url)
            if resp.status_code < 500:
                print("SearXNG is up.")
                return True
        except httpx.HTTPError:
            pass
        time.sleep(interval)

    print("SearXNG did not become ready in time.", file=sys.stderr)
    return False


def run_doctor() -> int:
    print("+ uv run osint doctor")
    result = subprocess.run(
        ["uv", "run", "osint", "doctor"],
        cwd=ROOT,
        check=False,
    )
    return int(result.returncode or 0)


def main() -> None:
    args = sys.argv[1:]
    if "--wait-only" in args:
        ok = wait_searxng()
        raise SystemExit(0 if ok else 1)
    if "--no-doctor" in args:
        ok = wait_searxng()
        raise SystemExit(0 if ok else 1)

    ok = wait_searxng()
    code = run_doctor()
    raise SystemExit(code if ok else max(code, 1))


if __name__ == "__main__":
    main()
