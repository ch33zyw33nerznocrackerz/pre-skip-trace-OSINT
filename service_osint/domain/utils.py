from __future__ import annotations

import re

_FREE_EMAIL_DOMAINS = frozenset(
    {
        "aol.com",
        "att.net",
        "comcast.net",
        "gmail.com",
        "googlemail.com",
        "hotmail.com",
        "icloud.com",
        "live.com",
        "mac.com",
        "mail.com",
        "me.com",
        "msn.com",
        "outlook.com",
        "proton.me",
        "protonmail.com",
        "verizon.net",
        "yahoo.com",
        "ymail.com",
    }
)

_DOMAIN_RE = re.compile(
    r"^(?:https?://)?(?:www\.)?([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+)$",
    re.IGNORECASE,
)


def normalize_domain(value: str) -> str | None:
    """Return a lowercase apex/host domain or None if invalid."""
    raw = value.strip().lower()
    if not raw or " " in raw:
        return None
    raw = raw.removeprefix("https://").removeprefix("http://").removeprefix("www.")
    raw = raw.split("/")[0].split(":")[0]
    if not _DOMAIN_RE.match(raw):
        return None
    return raw


def is_free_email_domain(domain: str) -> bool:
    return domain.strip().lower() in _FREE_EMAIL_DOMAINS


def domain_from_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    host = email.split("@", 1)[1].strip().lower()
    if is_free_email_domain(host):
        return None
    return normalize_domain(host)


def domain_from_employer(employer: str | None) -> str | None:
    """Only when employer string already looks like a hostname."""
    if not employer:
        return None
    candidate = employer.strip()
    if "." not in candidate or " " in candidate:
        return None
    return normalize_domain(candidate)


def resolve_scan_domain(
    *,
    domain: str | None = None,
    email: str | None = None,
    employer: str | None = None,
) -> str | None:
    """Pick the best corporate/owned domain to scan."""
    if domain:
        return normalize_domain(domain)
    from_email = domain_from_email(email)
    if from_email:
        return from_email
    return domain_from_employer(employer)
