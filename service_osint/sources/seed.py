from __future__ import annotations

from .bookmarks import DORK_TOOL_SOURCES, PEOPLE_SEARCH_SOURCES, PUBLIC_RECORD_SOURCES

DEFAULT_SOURCES: list[tuple[str, str, str, str, str]] = [
    *PUBLIC_RECORD_SOURCES,
    *PEOPLE_SEARCH_SOURCES,
    *DORK_TOOL_SOURCES,
]
