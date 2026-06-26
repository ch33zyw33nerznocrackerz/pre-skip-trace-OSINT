from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

Tier = Literal["free", "freemium", "paid", "self-host", "builtin"]


@dataclass(frozen=True)
class ApiKeySpec:
    env_var: str
    label: str
    tier: Tier
    signup_url: str
    category: str
    notes: str = ""

    def is_configured(self) -> bool:
        return bool((os.getenv(self.env_var) or "").strip())

    def tier_label(self) -> str:
        return {
            "free": "FREE",
            "freemium": "FREE tier",
            "paid": "PAID",
            "self-host": "SELF-HOST (free)",
            "builtin": "No key needed",
        }[self.tier]


# Chronological: infrastructure -> discovery -> enrichment -> collectors -> domain
API_KEY_SPECS: tuple[ApiKeySpec, ...] = (
    ApiKeySpec(
        env_var="SEARXNG_URL",
        label="SearXNG meta-search",
        tier="self-host",
        signup_url="https://docs.searxng.org/admin/installation.html",
        category="discovery",
        notes="Run: just docker-searxng (local Docker, no API key)",
    ),
    ApiKeySpec(
        env_var="SERPER_API_KEY",
        label="Serper (Google results API)",
        tier="freemium",
        signup_url="https://serper.dev/",
        category="discovery",
        notes="~2,500 free queries/month",
    ),
    ApiKeySpec(
        env_var="TAVILY_API_KEY",
        label="Tavily agent search",
        tier="freemium",
        signup_url="https://tavily.com/",
        category="discovery",
        notes="Free tier for dev/testing",
    ),
    ApiKeySpec(
        env_var="EXA_API_KEY",
        label="Exa neural search",
        tier="freemium",
        signup_url="https://exa.ai/",
        category="discovery",
        notes="Free tier with monthly credits",
    ),
    ApiKeySpec(
        env_var="BRAVE_API_KEY",
        label="Brave Search API",
        tier="freemium",
        signup_url="https://brave.com/search/api/",
        category="discovery",
        notes="Free tier (2,000 queries/mo)",
    ),
    ApiKeySpec(
        env_var="LINKUP_API_KEY",
        label="Linkup deep web search",
        tier="paid",
        signup_url="https://www.linkup.so/",
        category="discovery",
        notes="Paid API — trial may be available",
    ),
    ApiKeySpec(
        env_var="FIRECRAWL_API_KEY",
        label="Firecrawl search/scrape",
        tier="freemium",
        signup_url="https://www.firecrawl.dev/",
        category="discovery",
        notes="Free tier for search + scrape",
    ),
    ApiKeySpec(
        env_var="JINA_API_KEY",
        label="Jina Reader (page text)",
        tier="freemium",
        signup_url="https://jina.ai/reader/",
        category="enrichment",
        notes="Optional; r.jina.ai works without key at lower limits",
    ),
    ApiKeySpec(
        env_var="CHAOS_API_KEY",
        label="ProjectDiscovery Chaos (subdomains)",
        tier="free",
        signup_url="https://chaos.projectdiscovery.io/",
        category="domain",
        notes="Passive subdomain intel for subfinder",
    ),
    ApiKeySpec(
        env_var="COURTLISTENER_API_TOKEN",
        label="CourtListener / RECAP",
        tier="free",
        signup_url="https://www.courtlistener.com/help/api/",
        category="collectors",
        notes="Federal court docket API",
    ),
    ApiKeySpec(
        env_var="OPENCORPORATES_API_TOKEN",
        label="OpenCorporates",
        tier="freemium",
        signup_url="https://opencorporates.com/api_accounts/new",
        category="collectors",
        notes="Free tier limited; paid for production volume",
    ),
    ApiKeySpec(
        env_var="SEC_CONTACT_EMAIL",
        label="SEC EDGAR User-Agent email",
        tier="free",
        signup_url="https://www.sec.gov/os/webmaster-faq",
        category="collectors",
        notes="Required contact string for SEC EDGAR requests (not a secret)",
    ),
)

BUILTIN_PROVIDERS: tuple[ApiKeySpec, ...] = (
    ApiKeySpec(
        env_var="",
        label="DuckDuckGo HTML search",
        tier="builtin",
        signup_url="",
        category="discovery",
        notes="Always on — no configuration",
    ),
)


def configured_keys() -> list[ApiKeySpec]:
    return [s for s in API_KEY_SPECS if s.is_configured()]


def missing_keys(*, include_builtin: bool = False) -> list[ApiKeySpec]:
    missing = [s for s in API_KEY_SPECS if not s.is_configured()]
    if include_builtin:
        missing.extend(BUILTIN_PROVIDERS)
    return missing


def keys_by_category(specs: list[ApiKeySpec]) -> dict[str, list[ApiKeySpec]]:
    out: dict[str, list[ApiKeySpec]] = {}
    for spec in specs:
        out.setdefault(spec.category, []).append(spec)
    return out


def discovery_ready_count() -> tuple[int, int]:
    """Return (configured discovery providers, total optional discovery keys)."""
    discovery = [s for s in API_KEY_SPECS if s.category == "discovery"]
    ready = sum(1 for s in discovery if s.is_configured())
    return ready, len(discovery)
