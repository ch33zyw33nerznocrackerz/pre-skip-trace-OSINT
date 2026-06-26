"""Align SEARXNG_PORT, SEARXNG_URL, and SEARXNG_BASE_URL in .env."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
EXAMPLE_PATH = ROOT / ".env.example"

KEYS = {
    "SEARXNG_PORT": lambda p: p,
    "SEARXNG_URL": lambda p: f"http://127.0.0.1:{p}",
    "SEARXNG_BASE_URL": lambda p: f"http://127.0.0.1:{p}/",
}


def patch_env(port: str, path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"Missing {path} — run: copy .env.example .env")

    text = path.read_text(encoding="utf-8")
    for key, fn in KEYS.items():
        value = fn(port)
        pattern = rf"^{re.escape(key)}=.*$"
        replacement = f"{key}={value}"
        if re.search(pattern, text, flags=re.MULTILINE):
            text = re.sub(pattern, replacement, text, count=1, flags=re.MULTILINE)
        else:
            text = text.rstrip() + f"\n{replacement}\n"
    path.write_text(text, encoding="utf-8")
    print(f"Updated {path.name} — SearXNG on http://127.0.0.1:{port}")


def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        raise SystemExit("Usage: uv run python scripts/set_searxng_port.py <port>")
    patch_env(sys.argv[1], ENV_PATH)


if __name__ == "__main__":
    main()
