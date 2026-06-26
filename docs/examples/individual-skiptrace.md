# Individual skip-trace example

```bash
uv run osint seed-person

# 1. Generate search seeds
uv run osint dorks urls "Maria Garcia" --city "Phoenix" --state AZ
uv run osint discover person "Maria Garcia" --city Phoenix --state AZ

# 2. Open bookmarks manually
uv run osint sources list --category people-search
uv run osint sources list --category property --jurisdiction AZ

# 3. After verifying a lead (assessor + people-search corroboration):
uv run osint add-subject "Maria Garcia" --role "Individual defendant"
uv run osint add-address "Maria Garcia" "456 Verified St" --city Phoenix --state AZ \
  --source "Maricopa Assessor + TruePeopleSearch" --confidence 70 \
  --corroborations 2 --recent --tags residence --notes "Name match on deed"

uv run osint add-evidence "Maria Garcia" "Maricopa Assessor" "https://mcassessor.maricopa.gov/..." \
  --notes "Parcel owner matches subject"

# 4. Process server attempt log
uv run osint attempt "Maria Garcia" "2026-06-25 07:15" "No answer" --address-id 1 \
  --notes "Lights on, no answer at door"

uv run osint serve-plan "Maria Garcia"
uv run osint export html "Maria Garcia" out/maria-garcia-packet.html
```

## API keys (optional but useful)

Copy `.env.example` to `.env`:

- **SearXNG** — run locally: `docker run -d -p 8080:8080 searxng/searxng`
- **Serper** — https://serper.dev (free tier)
- **Brave** — https://api.search.brave.com
- **Linkup** — https://linkup.so
- **Firecrawl** — https://firecrawl.dev or `firecrawl login --browser`
