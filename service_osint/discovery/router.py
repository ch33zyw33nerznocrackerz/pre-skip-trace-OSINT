from __future__ import annotations

from .base import DiscoveryResult, SearchProvider
from .config import DiscoveryConfig
from .providers import (
    BraveProvider,
    DuckDuckGoProvider,
    ExaProvider,
    FirecrawlProvider,
    LinkupProvider,
    SearXNGProvider,
    SerperProvider,
    TavilyProvider,
)

DEFAULT_PROVIDER_ORDER = (
    "searxng",
    "serper",
    "tavily",
    "exa",
    "brave",
    "linkup",
    "firecrawl",
    "duckduckgo",
)


def build_providers(config: DiscoveryConfig | None = None) -> list[SearchProvider]:
    cfg = config or DiscoveryConfig.from_env()
    return [
        SearXNGProvider(cfg),
        SerperProvider(cfg),
        TavilyProvider(cfg),
        ExaProvider(cfg),
        BraveProvider(cfg),
        LinkupProvider(cfg),
        FirecrawlProvider(cfg),
        DuckDuckGoProvider(),
    ]


def discover(
    query: str,
    *,
    limit: int = 10,
    provider: str | None = None,
    config: DiscoveryConfig | None = None,
) -> list[DiscoveryResult]:
    providers = {p.name: p for p in build_providers(config)}
    if provider:
        chosen = providers.get(provider)
        if not chosen:
            return [DiscoveryResult(query=query, provider=provider, error=f"Unknown provider: {provider}")]
        return [chosen.search(query, limit=limit)]
    results: list[DiscoveryResult] = []
    for name in DEFAULT_PROVIDER_ORDER:
        p = providers[name]
        if p.available():
            results.append(p.search(query, limit=limit))
    if not results:
        return [
            DiscoveryResult(
                query=query,
                provider="none",
                error="No discovery providers available.",
            )
        ]
    return results


def list_providers(config: DiscoveryConfig | None = None) -> list[tuple[str, bool, str]]:
    cfg = config or DiscoveryConfig.from_env()
    notes = {
        "searxng": "SEARXNG_URL — self-host or public instance (free)",
        "serper": "SERPER_API_KEY — serper.dev (~2,500 free queries)",
        "tavily": "TAVILY_API_KEY — tavily.com agent search (free tier)",
        "exa": "EXA_API_KEY — exa.ai neural search (free tier)",
        "brave": "BRAVE_API_KEY — Brave Search API free tier",
        "linkup": "LINKUP_API_KEY — linkup.so deep web search",
        "firecrawl": "FIRECRAWL_API_KEY — firecrawl.dev search/scrape",
        "duckduckgo": "No key — always-on HTML search fallback",
    }
    return [(p.name, p.available(), notes.get(p.name, "")) for p in build_providers(cfg)]
