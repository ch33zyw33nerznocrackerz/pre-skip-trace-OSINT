from __future__ import annotations

import json
from pathlib import Path


def read_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]


def parse_subdomains(output_dir: Path) -> list[str]:
    hosts: set[str] = set()
    for name in ("subs.txt", "resolved.txt"):
        for line in read_lines(output_dir / name):
            host = line.split()[0] if line else ""
            if host and "." in host:
                hosts.add(host.lower())
    return sorted(hosts)


def parse_live_hosts(output_dir: Path) -> list[dict[str, str]]:
    path = output_dir / "live.json"
    if not path.is_file():
        return []
    hosts: list[dict[str, str]] = []
    for line in read_lines(path):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        url = str(row.get("url") or row.get("input") or "")
        if not url.startswith("http"):
            continue
        hosts.append(
            {
                "url": url,
                "title": str(row.get("title") or ""),
                "status": str(row.get("status_code") or row.get("status-code") or ""),
                "host": str(row.get("host") or ""),
            }
        )
    return hosts


def parse_tls_names(output_dir: Path) -> list[str]:
    path = output_dir / "tls.json"
    if not path.is_file():
        return []
    names: set[str] = set()
    for line in read_lines(path):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        for key in ("subject_cn", "subject_an", "san"):
            val = row.get(key)
            if isinstance(val, str) and val:
                names.add(val.lower())
            elif isinstance(val, list):
                names.update(str(v).lower() for v in val if v)
    return sorted(names)


def recon_lead_map(output_dir: Path) -> dict[str, set[str]]:
    """Map parsed recon artifacts into lead buckets."""
    urls: set[str] = set()
    for host in parse_subdomains(output_dir):
        urls.add(f"https://{host}")
    for row in parse_live_hosts(output_dir):
        urls.add(row["url"])
    for name in parse_tls_names(output_dir):
        if name.startswith("*."):
            name = name[2:]
        if "." in name and " " not in name:
            urls.add(f"https://{name}")
    return {"url": urls}
