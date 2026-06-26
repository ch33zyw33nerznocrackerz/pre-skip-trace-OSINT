from __future__ import annotations

from .base import CollectResult, capture_page
from .property_portals import BLACKBOOK_PROPERTY, resolve_property_portal


class PropertyCollector:
    name = "property"
    label = "County property / assessor portal (NETR fallback)"

    def collect(
        self,
        subject: str,
        *,
        capture: bool = True,
        wait_ms: int = 2500,
        state: str | None = None,
        city: str | None = None,
    ) -> CollectResult:
        plan = resolve_property_portal(state, city)
        loc = f"{city}, {plan.state}" if city else plan.state
        manual = (
            f'Search owner name "{subject}" on {plan.primary_name} ({loc}).',
            "If county portal is wrong, use NETR to find the correct assessor/recorder for that county.",
            "Verify parcel owner name matches subject before logging an address.",
            "Note mailing vs situs address; tag residence vs mailing in add-address.",
            f'Add hit: osint add-address "{subject}" "<address>" --city "{city or ""}" '
            f'--state {plan.state} --source "{plan.primary_name}"',
        )
        if plan.uses_netr_primary:
            manual = (
                f'No pinned assessor for {plan.state}; open NETR and pick county assessor/recorder.',
                f'Search owner "{subject}" on the county site linked from NETR.',
                *manual[2:],
            )

        extra = [BLACKBOOK_PROPERTY]
        if not plan.uses_netr_primary and plan.netr_url != plan.primary_url:
            extra.insert(0, plan.netr_url)

        shot_path, digest = (None, None)
        if capture:
            shot_path, digest = capture_page(plan.primary_url, f"property-{subject}-{plan.state}", wait_ms=wait_ms)

        notes = (
            f"{plan.primary_name} captured for owner search in {loc}. "
            + ("NETR used as primary portal for this state." if plan.uses_netr_primary else "NETR county directory linked.")
        )
        return CollectResult(
            collector=self.name,
            subject=subject,
            url=plan.primary_url,
            screenshot_path=shot_path,
            sha256=digest,
            notes=notes,
            manual_steps=manual,
            extra_urls=tuple(extra),
        )
