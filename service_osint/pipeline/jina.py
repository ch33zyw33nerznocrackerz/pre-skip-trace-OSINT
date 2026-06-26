from __future__ import annotations

import os

import httpx


def fetch_page_text(url: str, *, api_key: str | None = None, timeout: float = 25.0) -> str:
    """Fetch readable page text via Jina Reader (r.jina.ai)."""
    if not url.startswith("http"):
        url = f"https://{url}"
    reader_url = f"https://r.jina.ai/{url}"
    headers: dict[str, str] = {"Accept": "text/plain"}
    key = api_key or os.getenv("JINA_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(reader_url, headers=headers)
            resp.raise_for_status()
            return resp.text[:8000]
    except Exception:
        return ""


def enrich_urls_with_jina(
    urls: list[str],
    *,
    limit: int = 5,
    api_key: str | None = None,
) -> list[str]:
    """Pull clean text from top hit URLs for lead extraction."""
    seen: set[str] = set()
    chunks: list[str] = []
    for url in urls:
        if len(chunks) >= limit:
            break
        norm = url.split("#")[0].rstrip("/")
        if norm in seen or not norm.startswith("http"):
            continue
        seen.add(norm)
        text = fetch_page_text(norm, api_key=api_key)
        if text.strip():
            chunks.append(f"--- {norm} ---\n{text}")
    return chunks
