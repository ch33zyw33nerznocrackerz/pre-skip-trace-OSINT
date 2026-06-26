from __future__ import annotations

from .base import CollectResult, capture_page


class NvsosCollector:
    name = "nvsos"
    label = "Nevada Secretary of State entity search"

    def collect(
        self,
        subject: str,
        *,
        capture: bool = True,
        wait_ms: int = 2500,
        state: str | None = None,
        city: str | None = None,
    ) -> CollectResult:
        url = "https://www.nvsos.gov/sosentitysearch/CorpSearch.aspx"
        ucc_url = "https://www.nvsos.gov/sos/businesses/ucc-filings"
        manual = (
            f'Search entity/officer name "{subject}" in Nevada SOS.',
            "Record registered agent, officers, and principal address from the entity detail page.",
            "Run UCC search if debtor/secured-party clues are needed.",
            "Capture entity detail page: osint capture <subject> \"Nevada SOS\" <detail-url>",
        )
        shot_path, digest = (None, None)
        if capture:
            shot_path, digest = capture_page(url, f"nvsos-{subject}", wait_ms=wait_ms)
        return CollectResult(
            collector=self.name,
            subject=subject,
            url=url,
            screenshot_path=shot_path,
            sha256=digest,
            notes="Nevada SOS search portal captured. Add registered-agent/office addresses after verification.",
            manual_steps=manual,
            extra_urls=(ucc_url,),
        )
