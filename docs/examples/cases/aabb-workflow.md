# AABB service-support workflow

```bash
uv run osint seed-aabb
uv run osint sources list --jurisdiction NV
uv run osint sources list --category property

# Add only verified public-record leads:
uv run osint add-address "Asia Broadband, Inc." "<registered-agent-address>" --city "Las Vegas" --state NV --source "Nevada SOS" --confidence 75 --corroborations 2 --recent --tags registered-agent,office
uv run osint add-evidence "Asia Broadband, Inc." "Nevada SOS" "<public-record-url>" --notes "Registered agent record"

# After process server reports attempts:
uv run osint attempt "Asia Broadband, Inc." "2026-06-25 10:15" "Served registered agent" --address-id 1 --notes "Accepted by authorized agent"

uv run osint show "Asia Broadband, Inc."
uv run osint export html "Asia Broadband, Inc." out/aabb-service-packet.html
```
