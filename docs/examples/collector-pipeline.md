# Collector pipeline workflow

Legal OSINT pipeline: **collect → verify → log → packet**.

```bash
uv sync
uv run playwright install chromium
uv run osint seed-aabb
uv run osint sources list
```

## 1. Collect public-record leads

Each collector opens the right portal, captures a Playwright screenshot (SHA-256), and logs evidence + a `collection_runs` audit row.

```bash
# Corporate SEC/OTC
uv run osint collect sec "Asia Broadband" --create

# Nevada entity / registered agent
uv run osint collect nvsos "Asia Broadband, Inc." --create

# Individual property (assessor owner search)
uv run osint collect property "Chris Torres" --city "Las Vegas" --state NV --create

# Social / people-search entry points
uv run osint collect socials "Chris Torres" --city "Las Vegas" --create

uv run osint collect list
uv run osint collect runs "Chris Torres"
```

Use `--no-capture` to get URLs and manual steps without Playwright.

## 2. Verify and add addresses (manual)

Only add addresses after corroborating assessor, SOS, or court records:

```bash
uv run osint add-address "Chris Torres" "123 Example St" \
  --city "Las Vegas" --state NV --source "Clark County Assessor" \
  --confidence 70 --corroborations 2 --recent --tags residence
```

## 3. Log service attempts

```bash
uv run osint attempt "Chris Torres" "2026-06-25 07:20" "No answer" --address-id 1
uv run osint serve-plan "Chris Torres"
```

## 4. Export full packet

```bash
uv run osint packet "Chris Torres"
# → out/chris-torres-packet.html|.json|.csv|.pdf

uv run osint packet "Chris Torres" --formats html,pdf --out out/cases
```

## Pipeline diagram

```
collect sec/nvsos/property/socials
        ↓
  evidence + screenshot + collection_runs
        ↓
  manual verify → add-address / capture detail pages
        ↓
  attempt log (due diligence)
        ↓
  packet (HTML/JSON/CSV/PDF)
```
