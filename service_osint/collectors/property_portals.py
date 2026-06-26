from __future__ import annotations

from dataclasses import dataclass

# Direct assessor/recorder portals where we have a stable owner-search entry point.
KNOWN_ASSESSORS: dict[str, tuple[str, str]] = {
    "NV": (
        "Clark County Assessor (NV)",
        "https://www.clarkcountynv.gov/government/assessor/property_search/real_property_records.php",
    ),
    "CA": (
        "Los Angeles County Assessor (CA)",
        "https://portal.assessor.lacounty.gov/",
    ),
    "AZ": (
        "Maricopa County Assessor (AZ)",
        "https://mcassessor.maricopa.gov/",
    ),
    "TX": (
        "Harris County Appraisal District (TX)",
        "https://hcad.org/property-search/",
    ),
    "FL": (
        "Miami-Dade Property Search (FL)",
        "https://www.miamidade.gov/Apps/PA/PropertySearch/#/",
    ),
    "NY": (
        "NYC ACRIS Property (NY)",
        "https://a836-acris.nyc.gov/CP/",
    ),
    "WA": (
        "King County Parcel Viewer (WA)",
        "https://gismaps.kingcounty.gov/parcelviewer2/",
    ),
    "CO": (
        "Denver Assessor Property (CO)",
        "https://www.denvergov.org/property",
    ),
    "OR": (
        "Multnomah County Assessment & Taxation (OR)",
        "https://multco.us/assessment-taxation",
    ),
    "UT": (
        "Salt Lake County Assessor (UT)",
        "https://www.saltlakecounty.gov/assessor/",
    ),
}

NETR_BASE = "https://publicrecords.netronline.com/state"
BLACKBOOK_PROPERTY = "https://www.blackbookonline.info/Property.aspx"


@dataclass(frozen=True)
class PropertyPortalPlan:
    state: str
    primary_name: str
    primary_url: str
    netr_url: str
    uses_netr_primary: bool


def netr_state_url(state: str) -> str:
    return f"{NETR_BASE}/{state.upper()}"


def resolve_property_portal(state: str | None, city: str | None = None) -> PropertyPortalPlan:
    """Pick assessor portal or NETR state directory for property owner search."""
    st = (state or "NV").upper()
    if st in KNOWN_ASSESSORS:
        name, url = KNOWN_ASSESSORS[st]
        if city:
            name = f"{name} ({city})"
        return PropertyPortalPlan(
            state=st,
            primary_name=name,
            primary_url=url,
            netr_url=netr_state_url(st),
            uses_netr_primary=False,
        )
    netr = netr_state_url(st)
    label = f"NETR Online — {st} public records"
    if city:
        label = f"{label} ({city})"
    return PropertyPortalPlan(
        state=st,
        primary_name=label,
        primary_url=netr,
        netr_url=netr,
        uses_netr_primary=True,
    )


def list_property_states() -> list[tuple[str, str, str]]:
    """Return (state, primary portal name, source type) for all US states."""
    all_states = [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
    ]
    rows: list[tuple[str, str, str]] = []
    for st in all_states:
        plan = resolve_property_portal(st)
        source = "assessor" if not plan.uses_netr_primary else "netr"
        rows.append((st, plan.primary_name.split(" (")[0], source))
    return rows
