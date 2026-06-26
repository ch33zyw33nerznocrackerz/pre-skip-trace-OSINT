from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

APP_OUT = Path.home() / ".service-osint" / "captures"
APP_OUT.mkdir(parents=True, exist_ok=True)


def slugify(value: str) -> str:
    keep: list[str] = []
    for ch in value.lower():
        if ch.isalnum():
            keep.append(ch)
        elif ch in " ._-":
            keep.append("-")
    out = "".join(keep).strip("-")
    while "--" in out:
        out = out.replace("--", "-")
    return out or "item"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
