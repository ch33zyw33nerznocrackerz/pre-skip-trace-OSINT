from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DiscoveryConfig:
    searxng_url: str | None
    serper_api_key: str | None
    brave_api_key: str | None
    linkup_api_key: str | None
    firecrawl_api_key: str | None
    tavily_api_key: str | None
    exa_api_key: str | None
    jina_api_key: str | None
    opencorporates_api_token: str | None

    @classmethod
    def from_env(cls) -> "DiscoveryConfig":
        return cls(
            searxng_url=os.getenv("SEARXNG_URL") or os.getenv("SEARXNG_INSTANCE"),
            serper_api_key=os.getenv("SERPER_API_KEY"),
            brave_api_key=os.getenv("BRAVE_API_KEY") or os.getenv("BRAVE_SEARCH_API_KEY"),
            linkup_api_key=os.getenv("LINKUP_API_KEY"),
            firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY"),
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            exa_api_key=os.getenv("EXA_API_KEY"),
            jina_api_key=os.getenv("JINA_API_KEY"),
            opencorporates_api_token=os.getenv("OPENCORPORATES_API_TOKEN"),
        )

    def configured_providers(self) -> list[str]:
        out: list[str] = []
        if self.searxng_url:
            out.append("searxng")
        if self.serper_api_key:
            out.append("serper")
        if self.tavily_api_key:
            out.append("tavily")
        if self.exa_api_key:
            out.append("exa")
        if self.brave_api_key:
            out.append("brave")
        if self.linkup_api_key:
            out.append("linkup")
        if self.firecrawl_api_key:
            out.append("firecrawl")
        out.append("duckduckgo")
        return out
