# Full OSINT automation

## Interactive (easiest)

```bash
uv run osint
```

Prompts for subject info, shows a search plan, then runs everything automatically.

Equivalent: `uv run osint start`

## One-liner (non-interactive)

```bash
uv run osint run "Chris Torres" --city "Las Vegas" --state NV
```

## What runs automatically

1. **Subject** — creates or loads dossier
2. **Dork seeds** — saves Google dork search URLs as evidence
3. **Discovery** — runs all configured APIs (SearXNG, Serper, Brave, Linkup, Firecrawl) with person-tuned query
4. **Dork discovery** — runs top 3 dorks through discovery APIs
5. **Collectors** — auto-selected by entity type:
   - **person**: property, socials, people (TruePeopleSearch/FastPeopleSearch)
   - **company**: sec, nvsos
6. **Lead extraction** — phones, emails, address hints from snippets (stored as unverified `leads`)
7. **Packet export** — HTML, JSON, CSV, PDF to `out/`

## Examples

```bash
# Individual — full automation
uv run osint run "Chris Torres" --city "Las Vegas" --state NV --email "chris@example.com"

# Corporate
uv run osint run "Asia Broadband" --entity-type company --collectors sec,nvsos

# Dry run — preview steps only
uv run osint run-plan "Chris Torres" --city "Las Vegas" --state NV

# Fast mode — no screenshots, no export
uv run osint run "Chris Torres" --no-capture --no-export --no-discovery

# Review results
uv run osint leads "Chris Torres"
uv run osint runs "Chris Torres"
uv run osint show "Chris Torres"
uv run osint packet "Chris Torres"
```

## Guardrails

- **Leads are not addresses** — automation never calls `add-address`; you verify first
- **Public pages only** — no auth bypass, CAPTCHA defeat, or paywall scraping
- **Corroborate** — assessor + court + SOS before service

## Configure discovery APIs

Copy `.env.example` to `.env` and add keys. More providers = richer automation.
