from __future__ import annotations

import re
from html import unescape

import httpx

from ..base import DiscoveryResult, SearchHit

_LINK_RE = re.compile(
    r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_SNIPPET_RE = re.compile(
    r'class="result__snippet"[^>]*>(.*?)</(?:td|div|span)>',
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")


class DuckDuckGoProvider:
    """No-key web search fallback via DuckDuckGo HTML results."""

    name = "duckduckgo"

    def available(self) -> bool:
        return True

    def search(self, query: str, *, limit: int = 10) -> DiscoveryResult:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                resp = client.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": query, "b": "", "kl": ""},
                    headers=headers,
                )
                resp.raise_for_status()
                html = resp.text
        except Exception as exc:  # noqa: BLE001
            return DiscoveryResult(query=query, provider=self.name, error=str(exc))

        links = _LINK_RE.findall(html)
        snippets = [_TAG_RE.sub("", unescape(s)).strip() for s in _SNIPPET_RE.findall(html)]
        hits: list[SearchHit] = []
        for i, (url, title_raw) in enumerate(links[:limit]):
            title = _TAG_RE.sub("", unescape(title_raw)).strip()
            snippet = snippets[i] if i < len(snippets) else ""
            hits.append(
                SearchHit(
                    title=title or url,
                    url=url,
                    snippet=snippet[:500],
                    provider=self.name,
                    rank=i + 1,
                )
            )
        return DiscoveryResult(query=query, provider=self.name, hits=hits, raw_count=len(links))
