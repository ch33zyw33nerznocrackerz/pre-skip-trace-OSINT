from __future__ import annotations

import os
from urllib.parse import quote_plus

import httpx

from .base import CollectResult, capture_page

COURTLISTENER_WEB = "https://www.courtlistener.com/"
COURTLISTENER_API = "https://www.courtlistener.com/api/rest/v3/search/"


def _api_snippets(subject: str, token: str, limit: int = 5) -> list[str]:
    snippets: list[str] = []
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(
                COURTLISTENER_API,
                headers={"Authorization": f"Token {token}"},
                params={"q": subject, "type": "r", "page_size": limit},
            )
            resp.raise_for_status()
            data = resp.json()
        for item in data.get("results") or []:
            title = item.get("caseName") or item.get("case_name") or "Docket"
            court = item.get("court") or item.get("court_id") or ""
            date = item.get("dateFiled") or item.get("date_filed") or ""
            url = item.get("absolute_url") or ""
            if url and not url.startswith("http"):
                url = f"https://www.courtlistener.com{url}"
            snippets.append(f"{title} | {court} | {date} | {url}")
    except Exception:
        return []
    return snippets


class CourtCollector:
    name = "court"
    label = "CourtListener / RECAP federal docket search"

    def collect(
        self,
        subject: str,
        *,
        capture: bool = True,
        wait_ms: int = 2500,
        state: str | None = None,
        city: str | None = None,
    ) -> CollectResult:
        query = quote_plus(subject)
        if state:
            query = quote_plus(f"{subject} {state}")
        search_url = f"{COURTLISTENER_WEB}?q={query}&type=r"
        pacer_url = f"https://pacer.uscourts.gov/find-case/search-national-index"
        ncsc_url = "https://www.ncsc.org/information-and-resources/state-court-websites"

        manual = (
            f'Review CourtListener RECAP results for party name "{subject}".',
            "Check complaints, summons, and filings for address of service or residence.",
            "Cross-check state courts via NCSC directory if matter may be state-level.",
            "PACER may be required for sealed or non-RECAP federal cases (lawful access only).",
            f'Capture detail page: osint capture "{subject}" "CourtListener" <docket-url>',
        )

        api_notes: list[str] = []
        token = os.getenv("COURTLISTENER_API_TOKEN")
        if token:
            hits = _api_snippets(subject, token)
            if hits:
                api_notes.append("CourtListener API hits:")
                api_notes.extend(hits[:5])

        shot_path, digest = (None, None)
        if capture:
            shot_path, digest = capture_page(search_url, f"court-{subject}", wait_ms=wait_ms)

        notes = "CourtListener search captured. Review dockets for party addresses."
        if api_notes:
            notes += "\n" + "\n".join(api_notes)

        return CollectResult(
            collector=self.name,
            subject=subject,
            url=search_url,
            screenshot_path=shot_path,
            sha256=digest,
            notes=notes,
            manual_steps=manual,
            extra_urls=(pacer_url, ncsc_url),
        )
