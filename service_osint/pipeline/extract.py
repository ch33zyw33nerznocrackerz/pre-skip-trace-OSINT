from __future__ import annotations

import re

PHONE_RE = re.compile(
    r"(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}"
)
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# Rough US street line — leads only, not verified addresses.
STREET_RE = re.compile(
    r"\b\d{1,6}\s+[A-Za-z0-9][\w\s.'-]{2,40}"
    r"(?:\s(?:St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|Rd|Road|Ln|Lane|Way|Ct|Court|Pl|Place))\b\.?",
    re.IGNORECASE,
)
ZIP_RE = re.compile(r"\b\d{5}(?:-\d{4})?\b")


def extract_leads(text: str) -> dict[str, set[str]]:
    if not text:
        return {"phone": set(), "email": set(), "address": set(), "zip": set()}
    phones = {p.strip() for p in PHONE_RE.findall(text)}
    emails = {e.lower() for e in EMAIL_RE.findall(text)}
    streets = {s.strip() for s in STREET_RE.findall(text)}
    zips = set(ZIP_RE.findall(text))
    return {"phone": phones, "email": emails, "address": streets, "zip": zips}


def merge_lead_maps(*maps: dict[str, set[str]]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {"phone": set(), "email": set(), "address": set(), "zip": set()}
    for m in maps:
        for k, vals in m.items():
            out.setdefault(k, set()).update(vals)
    return out
