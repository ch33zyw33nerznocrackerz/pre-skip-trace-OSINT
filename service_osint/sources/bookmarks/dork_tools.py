from __future__ import annotations

# Google dork helpers and OSINT seed-discovery tools (manual use).
DORK_TOOL_SOURCES: list[tuple[str, str, str, str, str]] = [
    ("Google Hacking Database (GHDB)", "dork-tools", "US", "https://www.exploit-db.com/google-hacking-database", "Curated Google dork index for OSINT."),
    ("DorkSearch", "dork-tools", "US", "https://dorksearch.com/", "Dork builder and query helper."),
    ("Google Advanced Search", "dork-tools", "US", "https://www.google.com/advanced_search", "GUI for site/filetype/date filters."),
    ("Bing Advanced Search", "dork-tools", "US", "https://www.bing.com/search", "Alternate index; append operators manually."),
    ("DuckDuckGo Bangs", "dork-tools", "US", "https://duckduckgo.com/bangs", "Quick site-scoped searches."),
    ("OSINT Framework - People", "dork-tools", "US", "https://osintframework.com/", "People-search tool directory."),
    ("IntelTechniques Search Tools", "dork-tools", "US", "https://inteltechniques.com/tools/Search.html", "People/username/email search form builder."),
    ("Epieos", "dork-tools", "US", "https://epieos.com/", "Email/phone/account pivot (freemium)."),
    ("Holehe", "dork-tools", "US", "https://github.com/megadose/holehe", "Email registration checker (self-host)."),
    ("Maigret", "dork-tools", "US", "https://github.com/soxoj/maigret", "Username search across sites (self-host)."),
    ("SearXNG Public Instances", "search-api", "US", "https://searx.space/", "Find a SearXNG instance or self-host for meta-search."),
]
