# service-osint — chronological workflow (Windows PowerShell + Ubuntu bash)
# Usage: just --list
#        just setup
#        just subject="Jane Doe" city="Las Vegas" state=NV run-full

set dotenv-load := true
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]
set shell := ["bash", "-eu", "-c"]

# BuildKit = faster cached rebuilds (Docker Desktop enables by default)
export DOCKER_BUILDKIT := "1"
export COMPOSE_DOCKER_CLI_BUILD := "1"
export COMPOSE_BAKE := "true"

compose   := "docker compose -f docker/docker-compose.yml"
osint     := "uv run osint"
pytest    := "uv run python -m pytest"

# --- workflow variables (override: just subject="Name" ...) ---
subject   := "Jane Doe"
city      := "Las Vegas"
state     := "NV"
email     := "jane@acmecorp.com"
domain    := "acmecorp.com"
employer  := ""
phone     := ""
entity    := "person"
out       := "out"

# =============================================================================
# 0. HELP
# =============================================================================

default: doctor

list:
    @just --list

check: doctor

# Cross-platform status line
notify TEXT:
    uv run python -c "print('{{TEXT}}')"

# =============================================================================
# 1. SETUP
# =============================================================================

setup: setup-env install deps playwright
    @just notify "Setup complete. Next: just doctor"

[windows]
setup-env:
    if (!(Test-Path .env)) { Copy-Item .env.example .env; Write-Host "Created .env" } else { Write-Host ".env exists" }

[unix]
setup-env:
    test -f .env || cp .env.example .env
    echo ".env ready"

install:
    uv sync

deps: install

playwright:
    uv run playwright install chromium

# =============================================================================
# 2. VERIFY
# =============================================================================

health:
    {{osint}} health --init

health-json:
    {{osint}} health --json --init --probe-searxng

health-verbose:
    {{osint}} health --init --verbose --probe-searxng

doctor:
    {{osint}} doctor

# Wait for SearXNG then run doctor (after docker-up / searxng-reset)
doctor-docker:
    uv run python scripts/wait_searxng.py --doctor

wait-searxng:
    uv run python scripts/wait_searxng.py --wait-only

debug-env:
    {{osint}} debug-env

keys:
    {{osint}} keys --missing

keys-all:
    {{osint}} keys

keys-json:
    {{osint}} keys --missing --json

test:
    {{pytest}} -q

test-verbose:
    {{pytest}} -v

# =============================================================================
# 3. DOCKER
# =============================================================================

# Show what holds a host port (8080 = default SearXNG)
[windows]
ports-check PORT="8080":
    Write-Host "Docker containers on :{{PORT}}:"
    docker ps -a --filter "publish={{PORT}}" --format "table {{ "{{" }}.Names{{ "}}" }}\t{{ "{{" }}.Ports{{ "}}" }}\t{{ "{{" }}.Status{{ "}}" }}"
    Write-Host "`nWindows listeners on :{{PORT}}:"
    netstat -ano | findstr ":{{PORT}}"

[unix]
ports-check PORT="8080":
    echo "Docker containers on :{{PORT}}:"
    docker ps -a --filter "publish={{PORT}}" --format 'table {{ "{{" }}.Names{{ "}}" }}\t{{ "{{" }}.Ports{{ "}}" }}\t{{ "{{" }}.Status{{ "}}" }}'
    echo ""
    echo "Listeners on :{{PORT}}:"
    ss -tlnp | grep ":{{PORT}} " || true

# Repoint SearXNG when 8080 is busy (updates .env — all three vars stay aligned)
searxng-port PORT="8081":
    uv run python scripts/set_searxng_port.py {{PORT}}

docker-up:
    {{compose}} up -d

# SearXNG only — use after `just searxng-port 8081` if 8080 is taken
docker-searxng:
    {{compose}} up -d searxng

# Recreate SearXNG + wipe cache, wait, then doctor
searxng-reset:
    uv run python scripts/searxng_reset.py

# FOSS tools only — skip SearXNG if you already have one elsewhere on :8080
docker-foss-only:
    {{compose}} --profile tools up -d foss

# Build FOSS image with layer cache (no --no-cache)
docker-build:
    {{compose}} build foss

# Build + start FOSS (skips rebuild when image unchanged)
docker-foss:
    {{compose}} --profile tools up -d foss --build

# Force full rebuild — slow, use only when Dockerfile or tool versions change
docker-foss-rebuild:
    {{compose}} build --no-cache --pull=false foss
    {{compose}} --profile tools up -d foss

docker-ui:
    {{compose}} --profile ui up -d spiderfoot-web

docker-all: docker-up docker-foss doctor-docker
    @just notify "Docker stack up — see doctor output above"

# Bootstrap without starting SearXNG (already running on :8080 elsewhere)
bootstrap-foss: setup docker-foss-only doctor-docker test
    @just notify "Bootstrap done (FOSS only — using existing SearXNG at SEARXNG_URL)"

docker-down:
    {{compose}} --profile tools --profile ui down

docker-logs:
    {{compose}} logs -f

docker-ps:
    {{compose}} ps

# =============================================================================
# 4. SOURCES
# =============================================================================

sources-seed:
    {{osint}} sources seed

seed-person:
    {{osint}} seed-person

seed-aabb:
    {{osint}} seed-aabb

sources-list:
    {{osint}} sources list

sources-people:
    {{osint}} sources list --category people-search

sources-dorks:
    {{osint}} sources list --category dork-tools

sources-property:
    {{osint}} sources list --category property

# =============================================================================
# 5. SUBJECT
# =============================================================================

add-subject:
    {{osint}} add-subject "{{subject}}" --role "Individual defendant"

show:
    {{osint}} show "{{subject}}"

serve-plan:
    {{osint}} serve-plan "{{subject}}"

add-address street="123 Example St" source="Manual verification":
    {{osint}} add-address "{{subject}}" "{{street}}" "{{source}}" --city "{{city}}" --state "{{state}}" --confidence 65 --corroborations 2 --recent --tags residence

add-evidence url="https://example.gov/record":
    {{osint}} add-evidence "{{subject}}" "County Assessor" "{{url}}" --notes "Verified public record"

capture url="https://www.truepeoplesearch.com/":
    {{osint}} capture "{{subject}}" "TruePeopleSearch" "{{url}}" --notes "Manual search captured"

attempt attempted_at="2026-01-15" result="not_served" notes="Due diligence":
    {{osint}} attempt "{{subject}}" "{{attempted_at}}" "{{result}}" --notes "{{notes}}"

# =============================================================================
# 6. DORKS
# =============================================================================

dorks-list:
    {{osint}} dorks list "{{subject}}" --city "{{city}}" --state "{{state}}"

dorks-urls:
    {{osint}} dorks urls "{{subject}}" --city "{{city}}" --state "{{state}}"

# =============================================================================
# 7. DISCOVERY
# =============================================================================

discover-providers:
    {{osint}} discover providers

discover-person:
    {{osint}} discover person "{{subject}}" --city "{{city}}" --state "{{state}}"

discover-search query="\"{{subject}}\" {{city}} {{state}}":
    {{osint}} discover search "{{query}}"

# =============================================================================
# 8. DOMAIN RECON
# =============================================================================

domain-resolve:
    {{osint}} domain resolve --email "{{email}}"

domain-scan:
    {{osint}} domain scan "{{domain}}" --subject "{{subject}}" --create

domain-scan-email:
    {{osint}} domain scan --email "{{email}}" --subject "{{subject}}" --create

domain-scan-dry:
    {{osint}} domain scan "{{domain}}" --dry-run

# =============================================================================
# 9. COLLECTORS
# =============================================================================

collect-list:
    {{osint}} collect list

collect-runs:
    {{osint}} collect runs "{{subject}}"

collect-sec:
    {{osint}} collect sec "{{subject}}" --create

collect-nvsos:
    {{osint}} collect nvsos "{{subject}}" --create

collect-property:
    {{osint}} collect property "{{subject}}" --city "{{city}}" --state "{{state}}" --create

collect-court:
    {{osint}} collect court "{{subject}}" --state "{{state}}" --create

collect-opencorp:
    {{osint}} collect opencorp "{{subject}}" --create

collect-socials:
    {{osint}} collect socials "{{subject}}" --city "{{city}}" --create

collect-property-states:
    {{osint}} collect property-states

collect-all: collect-sec collect-nvsos collect-property collect-court collect-socials
    @just notify "Collectors finished for {{subject}}"

# =============================================================================
# 10. FOSS
# =============================================================================

foss-list:
    {{osint}} foss list

foss-guide:
    {{osint}} foss install-guide

foss-guide-md:
    {{osint}} foss install-guide -o docs/foss-install.md

foss-spiderfoot-email:
    {{osint}} foss run spiderfoot-email --email "{{email}}"

foss-spiderfoot-domain:
    {{osint}} foss run spiderfoot-domain --domain "{{domain}}"

foss-photon url="https://example.com":
    {{osint}} foss run photon --url "{{url}}"

foss-subfinder:
    {{osint}} foss run subfinder --domain "{{domain}}"

# =============================================================================
# 11. SOCIAL PAI
# =============================================================================

social-tools:
    {{osint}} social tools

social-usernames:
    {{osint}} social usernames "{{subject}}" --email "{{email}}"

social-scan:
    {{osint}} social scan "{{subject}}" --email "{{email}}" --phone "{{phone}}" --create

# =============================================================================
# 12. PIPELINE
# =============================================================================

interactive:
    {{osint}}

start:
    {{osint}} start

run-plan:
    {{osint}} run-plan "{{subject}}" --city "{{city}}" --state "{{state}}" --entity-type "{{entity}}"

run-basic:
    {{osint}} run "{{subject}}" --city "{{city}}" --state "{{state}}" --entity-type "{{entity}}"

run-full:
    {{osint}} run "{{subject}}" --city "{{city}}" --state "{{state}}" --email "{{email}}" --entity-type "{{entity}}" --foss --domain-recon --social-pai --domain "{{domain}}"

run-company:
    {{osint}} run "{{subject}}" --entity-type company --foss

leads:
    {{osint}} leads "{{subject}}"

runs:
    {{osint}} runs "{{subject}}"

# =============================================================================
# 13. EXPORT
# =============================================================================

packet:
    {{osint}} packet "{{subject}}"

packet-pdf:
    {{osint}} packet-pdf "{{subject}}"

export-html file="packet.html":
    {{osint}} export html "{{subject}}" {{out}}/{{file}}

export-json file="packet.json":
    {{osint}} export json "{{subject}}" {{out}}/{{file}}

export-csv file="packet.csv":
    {{osint}} export csv "{{subject}}" {{out}}/{{file}}

export-pdf file="packet.pdf":
    {{osint}} export pdf "{{subject}}" {{out}}/{{file}}

export-all: export-html export-json export-csv export-pdf
    @just notify "Exported all formats to {{out}}/"

# =============================================================================
# 14. END-TO-END WORKFLOWS
# =============================================================================

bootstrap: setup docker-all test
    @just notify "Bootstrap done."

case-init: sources-seed add-subject dorks-urls discover-person discover-providers
    @just notify "Case initialized for {{subject}}"

case-recon: domain-scan-email social-scan collect-all
    @just notify "Recon pass done for {{subject}}"

case-run: run-full packet
    @just notify "Pipeline + packet for {{subject}}"

workflow: bootstrap case-init case-recon case-run
    @just notify "Full workflow complete for {{subject}}"

workflow-manual: case-init dorks-urls discover-person collect-property show serve-plan export-html
    @just notify "Manual workflow complete for {{subject}}"
