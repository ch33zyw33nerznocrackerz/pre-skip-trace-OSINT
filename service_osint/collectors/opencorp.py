from __future__ import annotations

import os
from urllib.parse import quote_plus

import httpx

from .base import CollectResult, capture_page

OPENCORP_WEB = "https://opencorporates.com/companies"
OPENCORP_API = "https://api.opencorporates.com/v0.4/companies/search"


def _api_hits(subject: str, token: str, limit: int = 5) -> list[str]:
    lines: list[str] = []
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(
                OPENCORP_API,
                params={"q": subject, "api_token": token, "per_page": limit},
            )
            resp.raise_for_status()
            data = resp.json()
        for co in (data.get("results") or {}).get("companies") or []:
            c = co.get("company") or co
            name = c.get("name") or ""
            juris = c.get("jurisdiction_code") or ""
            num = c.get("company_number") or ""
            addr = (c.get("registered_address_in_full") or "")[:200]
            url = c.get("opencorporates_url") or ""
            lines.append(f"{name} | {juris} #{num} | {addr} | {url}")
    except Exception:
        return []
    return lines


class OpenCorpCollector:
    name = "opencorp"
    label = "OpenCorporates officer / registered-agent search"

    def collect(
        self,
        subject: str,
        *,
        capture: bool = True,
        wait_ms: int = 2500,
        state: str | None = None,
        city: str | None = None,
    ) -> CollectResult:
        q = quote_plus(subject)
        if state:
            q = quote_plus(f"{subject} {state}")
        search_url = f"{OPENCORP_WEB}?q={q}"

        manual = (
            f'Search OpenCorporates for "{subject}" and review officers / registered agents.',
            "Cross-check registered-agent address with SOS filing and assessor.",
            "Use for corporate defendants or individuals tied to active companies.",
            f'Add verified address: osint add-address "{subject}" "<address>" --source "OpenCorporates"',
        )

        notes_parts = ["OpenCorporates search captured. Review officer and agent records."]
        token = os.getenv("OPENCORPORATES_API_TOKEN")
        if token:
            hits = _api_hits(subject, token)
            if hits:
                notes_parts.append("API matches:")
                notes_parts.extend(hits[:5])

        shot_path, digest = (None, None)
        if capture:
            shot_path, digest = capture_page(search_url, f"opencorp-{subject}", wait_ms=wait_ms)

        return CollectResult(
            collector=self.name,
            subject=subject,
            url=search_url,
            screenshot_path=shot_path,
            sha256=digest,
            notes="\n".join(notes_parts),
            manual_steps=manual,
            extra_urls=(f"{OPENCORP_WEB}?jurisdiction_code=us_nv&q={q}",),
        )
