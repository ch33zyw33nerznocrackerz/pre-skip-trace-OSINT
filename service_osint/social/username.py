from __future__ import annotations

import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _normalize_token(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return _NON_ALNUM.sub("", text.lower())


def guess_usernames(name: str, email: str | None = None, *, limit: int = 6) -> list[str]:
    """Generate username candidates from legal name and email local-part."""
    seen: set[str] = set()
    out: list[str] = []

    def add(candidate: str) -> None:
        c = candidate.strip().lower()
        if len(c) < 3 or c in seen:
            return
        seen.add(c)
        out.append(c)

    if email and "@" in email:
        local = email.split("@", 1)[0]
        add(local)
        add(local.replace(".", ""))
        add(local.replace(".", "_"))
        add(local.replace(".", "-"))

    parts = [_normalize_token(p) for p in name.split() if _normalize_token(p)]
    if not parts:
        return out[:limit]

    first, *rest = parts
    last = parts[-1] if len(parts) > 1 else ""
    middle = parts[1] if len(parts) > 2 else ""

    if first and last:
        add(f"{first}{last}")
        add(f"{first}.{last}")
        add(f"{first}_{last}")
        add(f"{first}-{last}")
        add(f"{first[0]}{last}")
        add(f"{last}{first}")
    if first:
        add(first)
    if last and last != first:
        add(last)
    if middle:
        add(f"{first}{middle[0]}{last}" if last else f"{first}{middle}")

    return out[:limit]
