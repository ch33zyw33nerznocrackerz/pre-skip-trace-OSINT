# Individual skip-trace workflow

Lawful OSINT for process servers locating **individuals**. Public records + people-search bookmarks + tiered discovery APIs.

## Install

```bash
cd C:\Users\roger\Documents\code\my-code\OSINT\pre-skip-trace-OSINT
copy .env.example .env
# Add API keys for Serper, Brave, Linkup, Firecrawl as you get them
uv sync
uv run playwright install chromium
uv run osint --help
```

Data: `~/.service-osint/case.db` · Screenshots: `~/.service-osint/captures/`

## Docker stack (SearXNG + SpiderFoot + Photon)

Self-host discovery and FOSS crawlers alongside the CLI:

```bash
cd C:\Users\roger\Documents\code\my-code\OSINT\pre-skip-trace-OSINT
copy .env.example .env
# FOSS_DOCKER=1 and SEARXNG_URL are already set in .env.example

docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose.yml --profile tools up -d foss

# Optional SpiderFoot web UI at http://127.0.0.1:5001
docker compose -f docker/docker-compose.yml --profile ui up -d spiderfoot-web

uv sync
uv run osint foss list
uv run osint foss run photon --url "https://example.com" --dry-run
```

| Service | Port | Purpose |
|---------|------|---------|
| **searxng** | 8080 | Meta-search for `osint discover` (`SEARXNG_URL`) |
| **foss** | — | SpiderFoot + Photon CLI via `FOSS_DOCKER=1` |
| **spiderfoot-web** | 5001 | Optional browser UI (`--profile ui`) |

Local installs (no Docker): clone [SpiderFoot](https://github.com/smicallef/spiderfoot) and [Photon](https://github.com/s0md3v/Photon), then set `SPIDERFOOT_DIR` and `PHOTON_DIR` in `.env` and unset `FOSS_DOCKER`.

Pipeline / interactive: enable FOSS with `osint run "Name" --email x@y.com --foss` or answer yes in the wizard.

## Social PAI (platform discovery)

Automated discovery of **publicly available** social profiles and account registrations across hundreds of platforms — using only lawful, public checks (no credential bypass):

```bash
uv run osint social tools
uv run osint social usernames "Jane Doe" --email jane@gmail.com
uv run osint social scan "Jane Doe" --email jane@gmail.com --phone 7025550100 --create
uv run osint run "Jane Doe" --email jane@gmail.com --social-pai
```

| Tool | Seed | Coverage |
|------|------|----------|
| **Sherlock** | username | 400+ sites |
| **Maigret** | username | Deep metadata (`--full`) |
| **holehe** | email | Registration checks |
| **socialscan** | email / username | Major platforms |
| **Ignorant** | phone | Instagram, Snapchat, etc. |

Usernames are auto-guessed from legal name and email local-part. All hits are **unverified leads** — corroborate with assessor, court, or SOS records before service. Do not contact subjects via discovered accounts.

## Project layout

```
osint/
├── .env.example
├── docker/
│   ├── docker-compose.yml      # SearXNG, foss (SpiderFoot+Photon), optional UI
│   ├── foss/Dockerfile
│   └── searxng/settings.yml
├── config/foss_tools.yaml
├── pyproject.toml
├── docs/examples/              # Workflow guides
│   ├── individual-skiptrace.md
│   └── cases/aabb-workflow.md
└── service_osint/
    ├── pipeline/               # Full automation orchestrator
    ├── collectors/             # SEC, NV SOS, property, socials, people
    ├── cli/
    │   ├── collect_cmd.py
    │   ├── packet_cmd.py
    │   └── ...
    ├── core/                   # SQLite models, scoring, DB
    ├── capture/                # Playwright evidence screenshots
    ├── export/                 # HTML / JSON / CSV / PDF packets
    ├── sources/
    │   ├── bookmarks/          # Public records, people search, dork tools
    │   ├── dorks.py
    │   └── seed.py
    ├── discovery/
    │   ├── providers/          # SearXNG, Serper, Brave, Linkup, Firecrawl
    │   ├── router.py
    │   └── config.py
    ├── foss/                   # SpiderFoot + Photon runners (local or Docker)
    └── utils/
```

## Interactive mode (recommended)

```bash
uv run osint
# or
uv run osint start
```

You'll be prompted for:
- Person or company
- Name, city, state, phone, email, employer
- Aliases
- Screenshot / discovery / packet options

Then the tool **searches automatically** (dorks, APIs, collectors, leads, packet).

## Full automation (non-interactive)

```bash
uv run osint run "Chris Torres" --city "Las Vegas" --state NV
uv run osint run "Asia Broadband" --entity-type company
uv run osint run-plan "Chris Torres" --city "Las Vegas" --state NV
uv run osint leads "Chris Torres"
```

See [docs/examples/full-automation.md](docs/examples/full-automation.md).

## Collector pipeline (next stage)

```bash
uv run osint collect sec "Asia Broadband" --create
uv run osint collect nvsos "Asia Broadband, Inc."
uv run osint collect property "Chris Torres" --city "Las Vegas" --state NV --create
uv run osint collect socials "Chris Torres" --city "Las Vegas"
uv run osint collect runs "Chris Torres"

# After manual verification + add-address / attempt logging:
uv run osint packet "Chris Torres"
# → out/chris-torres-packet.html, .json, .csv, .pdf
```

See [docs/examples/collector-pipeline.md](docs/examples/collector-pipeline.md).

## Fast start — individual

```bash
uv run osint seed-person
uv run osint sources list --category people-search
uv run osint add-subject "Jane Doe" --role "Individual defendant" --notes "NV small-claims"

# Dork seeds + ready URLs
uv run osint dorks list "Jane Doe" --city "Las Vegas" --state NV
uv run osint dorks urls "Jane Doe" --city "Las Vegas" --state NV

# Tiered discovery (uses all configured providers)
uv run osint discover providers
uv run osint discover person "Jane Doe" --city "Las Vegas" --state NV
uv run osint discover search "\"Jane Doe\" Las Vegas NV site:truepeoplesearch.com" --provider serper

# Build dossier from verified leads only
uv run osint add-address "Jane Doe" "123 Example St" --city "Las Vegas" --state NV \
  --source "Clark County Assessor" --confidence 65 --corroborations 2 --recent --tags residence
uv run osint add-evidence "Jane Doe" "County Assessor" "https://example.gov/record" --notes "Owner name match"
uv run osint capture "Jane Doe" "TruePeopleSearch" "https://www.truepeoplesearch.com/" --notes "Manual search captured"
uv run osint show "Jane Doe"
uv run osint serve-plan "Jane Doe"
uv run osint export html "Jane Doe" out/jane-doe-packet.html
```

## Discovery providers (free tiers)

| Provider | Env var | Notes |
|----------|---------|-------|
| SearXNG | `SEARXNG_URL` | `docker compose -f docker/docker-compose.yml up -d` |
| Serper | `SERPER_API_KEY` | serper.dev — Google results API |
| Brave | `BRAVE_API_KEY` | api.search.brave.com |
| Linkup | `LINKUP_API_KEY` | linkup.so deep search |
| Firecrawl | `FIRECRAWL_API_KEY` | firecrawl.dev search/scrape |

Run `osint discover providers` to see what's configured.

## Source categories

After `osint sources seed`:

- `people-search` — TruePeopleSearch, FastPeopleSearch, Spokeo, Whitepages, etc.
- `dork-tools` — GHDB, DorkSearch, OSINT Framework, IntelTechniques
- `property`, `court`, `business`, `voter` — public records
- `social` — LinkedIn/Facebook (manual review)

```bash
uv run osint sources list --category people-search
uv run osint sources list --category dork-tools
```

## Guardrails

Use only public records, licensed databases you are authorized to access, and process-server notes. Do not bypass auth/CAPTCHAs, scrape behind paywalls, impersonate subjects, or automate harassment. People-search hits are **leads** — corroborate with assessor, court, or SOS records before service.

## Suggested workflow

1. `add-subject` + `sources seed`
2. `dorks urls` and `discover person` for seed leads
3. Manual search people-search + county property/court portals
4. `add-address` / `add-evidence` / `capture` for verified hits only
5. `attempt` to log process-server due diligence
6. `export html` for the service packet
