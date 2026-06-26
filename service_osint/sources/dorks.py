from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus


@dataclass(frozen=True)
class DorkQuery:
    label: str
    query: str
    purpose: str


def _q(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


def person_dorks(
    name: str,
    city: str | None = None,
    state: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    employer: str | None = None,
) -> list[DorkQuery]:
    """Generate Google-style dork seeds for individual skip-trace."""
    loc = _q([city, state])
    quoted_name = f'"{name}"'
    dorks: list[DorkQuery] = [
        DorkQuery("Exact name + location", _q([quoted_name, loc]), "Broad web hits tying name to geography."),
        DorkQuery("LinkedIn profile", f'site:linkedin.com/in {quoted_name} {loc}', "Employment and metro area hints."),
        DorkQuery("Facebook profile", f'site:facebook.com {quoted_name} {loc}', "Social presence and check-ins."),
        DorkQuery("TruePeopleSearch mirror", f'site:truepeoplesearch.com {quoted_name}', "Aggregator page discovery."),
        DorkQuery("FastPeopleSearch mirror", f'site:fastpeoplesearch.com {quoted_name}', "Alternate aggregator hits."),
        DorkQuery("Whitepages directory", f'site:whitepages.com {quoted_name} {loc}', "Directory listing discovery."),
        DorkQuery("Court / legal PDF", f'{quoted_name} {loc} (filetype:pdf OR filetype:doc) (court OR complaint OR summons)', "Litigation and filing address clues."),
        DorkQuery("Property / assessor", f'{quoted_name} {loc} (assessor OR "property owner" OR deed)', "Real property ownership leads."),
        DorkQuery("Professional license", f'{quoted_name} {state or ""} (license OR "professional license" OR bar OR realtor)', "Regulated-profession address filings."),
        DorkQuery("Obituary / relatives", f'{quoted_name} {loc} (obituary OR "survived by")', "Relative graph for alternate addresses."),
        DorkQuery("Resume / CV leak", f'{quoted_name} {loc} (resume OR cv OR curriculum vitae) filetype:pdf', "Self-reported contact info."),
        DorkQuery("GitHub / dev footprint", f'site:github.com {quoted_name} OR {email or ""}', "Email/username pivots for tech subjects."),
        DorkQuery("Instagram bio", f'site:instagram.com {quoted_name}', "Social handle discovery."),
        DorkQuery("Twitter / X", f'(site:twitter.com OR site:x.com) {quoted_name}', "Public posts and bios."),
        DorkQuery("TikTok", f'site:tiktok.com {quoted_name}', "Short-form social presence."),
        DorkQuery("Reddit", f'site:reddit.com {quoted_name} {loc}', "Forum posts and location hints."),
        DorkQuery("News mention", f'{quoted_name} {loc} (site:news OR site:patch.com OR "press release")', "Event/address mentions in media."),
    ]
    if phone:
        dorks.append(DorkQuery("Phone number", f'"{phone}" OR {phone.replace("-", "")}', "Reverse-phone web traces."))
    if email:
        dorks.append(DorkQuery("Email address", f'"{email}" OR intext:"{email}"', "Account registrations and leaks."))
        dorks.append(DorkQuery("Email + name", f'{quoted_name} "{email}"', "Corroborate identity match."))
    if employer:
        dorks.append(DorkQuery("Employer tie", f'{quoted_name} "{employer}" {loc}', "Worksite service or mail-room leads."))
    return dorks


def google_search_url(query: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(query)}"


def ddg_search_url(query: str) -> str:
    return f"https://duckduckgo.com/?q={quote_plus(query)}"


def truepeoplesearch_url(name: str, city: str | None = None, state: str | None = None) -> str:
    parts = name.strip().replace(" ", "-")
    if city and state:
        return f"https://www.truepeoplesearch.com/results?name={quote_plus(name)}&citystatezip={quote_plus(f'{city}, {state}')}"
    return f"https://www.truepeoplesearch.com/results?name={quote_plus(name)}"


def fastpeoplesearch_url(name: str, city: str | None = None, state: str | None = None) -> str:
    slug = name.strip().replace(" ", "-")
    if city and state:
        return f"https://www.fastpeoplesearch.com/name/{slug}_{city.lower().replace(' ', '-')}_{state.lower()}"
    return f"https://www.fastpeoplesearch.com/name/{slug}"
