from __future__ import annotations

from urllib.parse import quote_plus

from .base import CollectResult, capture_page


class SocialsCollector:
    name = "socials"
    label = "LinkedIn / Facebook people search (manual review)"

    def collect(
        self,
        subject: str,
        *,
        capture: bool = True,
        wait_ms: int = 2500,
        state: str | None = None,
        city: str | None = None,
    ) -> CollectResult:
        keywords = subject if not city else f"{subject} {city}"
        linkedin = f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(keywords)}"
        facebook = f"https://www.facebook.com/search/people/?q={quote_plus(keywords)}"
        tps = f"https://www.truepeoplesearch.com/results?name={quote_plus(subject)}"
        manual = (
            f'Review LinkedIn/Facebook results for "{subject}"; login walls are expected.',
            "Use employment/metro hints only as leads — corroborate with assessor or court records.",
            "Do not contact or interact with the subject via social accounts.",
            "Add corroborated address: osint add-address ... --source \"assessor + people-search\"",
        )
        shot_path, digest = (None, None)
        if capture:
            shot_path, digest = capture_page(linkedin, f"socials-{subject}", wait_ms=wait_ms)
        return CollectResult(
            collector=self.name,
            subject=subject,
            url=linkedin,
            screenshot_path=shot_path,
            sha256=digest,
            notes="Social search entry captured (LinkedIn). Facebook/people-search URLs provided for manual review.",
            manual_steps=manual,
            extra_urls=(facebook, tps),
        )
