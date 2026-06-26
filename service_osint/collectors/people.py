from __future__ import annotations

from urllib.parse import quote_plus

from .base import CollectResult, capture_page


class PeopleCollector:
    name = "people"
    label = "TruePeopleSearch + FastPeopleSearch portals"

    def collect(
        self,
        subject: str,
        *,
        capture: bool = True,
        wait_ms: int = 2500,
        state: str | None = None,
        city: str | None = None,
    ) -> CollectResult:
        if city and state:
            tps = (
                f"https://www.truepeoplesearch.com/results?name={quote_plus(subject)}"
                f"&citystatezip={quote_plus(f'{city}, {state}')}"
            )
            slug = subject.strip().replace(" ", "-")
            fps = (
                f"https://www.fastpeoplesearch.com/name/{slug}_"
                f"{city.lower().replace(' ', '-')}_{state.lower()}"
            )
        else:
            tps = f"https://www.truepeoplesearch.com/results?name={quote_plus(subject)}"
            fps = f"https://www.fastpeoplesearch.com/name/{subject.strip().replace(' ', '-')}"

        manual = (
            f'Review TruePeopleSearch/FastPeopleSearch for "{subject}".',
            "Cross-check any address with county assessor before add-address.",
            "People-search data is a lead only — not proof of residence.",
        )
        shot_path, digest = (None, None)
        if capture:
            shot_path, digest = capture_page(tps, f"people-{subject}", wait_ms=wait_ms)
        return CollectResult(
            collector=self.name,
            subject=subject,
            url=tps,
            screenshot_path=shot_path,
            sha256=digest,
            notes="People-search portals captured. Verify all hits against primary records.",
            manual_steps=manual,
            extra_urls=(fps,),
        )
