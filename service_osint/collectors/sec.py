from __future__ import annotations

from urllib.parse import quote_plus

from .base import CollectResult, capture_page


class SecCollector:
    name = "sec"
    label = "SEC EDGAR full-text search"

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
        url = f"https://www.sec.gov/edgar/search/#/q={query}"
        otc_url = f"https://www.otcmarkets.com/search?q={query}"
        manual = (
            f'Run EDGAR search for "{subject}" and review 10-K/10-Q, 8-K, DEF 14A exhibits.',
            "Check officer/director signatures, related-party disclosures, and transfer-agent sections.",
            "Cross-check OTC Markets profile if issuer is OTC.",
            "Add verified addresses with: osint add-address ... --source SEC EDGAR",
        )
        shot_path, digest = (None, None)
        if capture:
            shot_path, digest = capture_page(url, f"sec-{subject}", wait_ms=wait_ms)
        return CollectResult(
            collector=self.name,
            subject=subject,
            url=url,
            screenshot_path=shot_path,
            sha256=digest,
            notes="EDGAR search portal captured. Review filings manually; do not treat search page as proof of address.",
            manual_steps=manual,
            extra_urls=(otc_url,),
        )
