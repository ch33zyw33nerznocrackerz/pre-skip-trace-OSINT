from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from service_osint.core.models import Defendant


def defendant_payload(defendant: Defendant) -> dict:
    return {
        "defendant": {
            "name": defendant.name,
            "role": defendant.role,
            "entity_type": defendant.entity_type,
            "notes": defendant.notes,
        },
        "aliases": [a.alias for a in defendant.aliases],
        "addresses": [
            {
                "id": a.id,
                "score": a.confidence,
                "address": a.address,
                "city": a.city,
                "state": a.state,
                "postal_code": a.postal_code,
                "source": a.source,
                "last_seen": a.last_seen,
                "tags": a.tags,
                "notes": a.notes,
            }
            for a in sorted(defendant.addresses, key=lambda x: x.confidence, reverse=True)
        ],
        "evidence": [
            {
                "id": e.id,
                "source": e.source_name,
                "url": e.url,
                "captured_at": e.captured_at.isoformat(),
                "file_path": e.file_path,
                "sha256": e.sha256,
                "notes": e.notes,
            }
            for e in defendant.evidence
        ],
        "service_attempts": [
            {
                "id": a.id,
                "address_id": a.address_id,
                "attempted_at": a.attempted_at,
                "result": a.result,
                "notes": a.server_notes,
            }
            for a in defendant.attempts
        ],
        "leads": [
            {
                "id": lead.id,
                "type": lead.lead_type,
                "value": lead.value,
                "confidence": lead.confidence,
                "source": lead.source,
                "verified": lead.verified,
            }
            for lead in sorted(defendant.leads, key=lambda x: x.confidence, reverse=True)
        ],
    }


def write_json(defendant: Defendant, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(defendant_payload(defendant), indent=2, ensure_ascii=False), encoding="utf-8")


def write_addresses_csv(defendant: Defendant, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "defendant",
                "role",
                "type",
                "address_id",
                "address",
                "city",
                "state",
                "postal_code",
                "score",
                "source",
                "last_seen",
                "tags",
                "notes",
            ]
        )
        for a in sorted(defendant.addresses, key=lambda x: x.confidence, reverse=True):
            w.writerow(
                [
                    defendant.name,
                    defendant.role,
                    defendant.entity_type,
                    a.id,
                    a.address,
                    a.city,
                    a.state,
                    a.postal_code,
                    a.confidence,
                    a.source,
                    a.last_seen,
                    a.tags,
                    a.notes,
                ]
            )


def render_html_packet(defendant: Defendant) -> str:
    p = defendant_payload(defendant)

    def esc(x: object) -> str:
        return html.escape("" if x is None else str(x))

    rows = "".join(
        f"<tr><td>{esc(a['id'])}</td><td>{esc(a['score'])}</td><td>{esc(a['address'])}</td>"
        f"<td>{esc(a['city'])}, {esc(a['state'])} {esc(a['postal_code'])}</td><td>{esc(a['source'])}</td>"
        f"<td>{esc(a['last_seen'])}</td><td>{esc(a['tags'])}</td><td>{esc(a['notes'])}</td></tr>"
        for a in p["addresses"]
    )
    evrows = "".join(
        f"<tr><td>{esc(e['id'])}</td><td>{esc(e['source'])}</td>"
        f"<td><a href='{esc(e['url'])}'>{esc(e['url'])}</a></td><td>{esc(e['captured_at'])}</td>"
        f"<td>{esc(e['file_path'])}</td><td><code>{esc(e['sha256'])}</code></td><td>{esc(e['notes'])}</td></tr>"
        for e in p["evidence"]
    )
    atrows = "".join(
        f"<tr><td>{esc(a['id'])}</td><td>{esc(a['address_id'])}</td><td>{esc(a['attempted_at'])}</td>"
        f"<td>{esc(a['result'])}</td><td>{esc(a['notes'])}</td></tr>"
        for a in p["service_attempts"]
    )
    leadrows = "".join(
        f"<tr><td>{esc(l['id'])}</td><td>{esc(l['type'])}</td><td>{esc(l['value'])}</td>"
        f"<td>{esc(l['confidence'])}</td><td>{esc(l['source'])}</td><td>{esc(l['verified'])}</td></tr>"
        for l in p["leads"]
    )
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>Service Packet - {esc(defendant.name)}</title>
<style>
body{{font-family:Arial,sans-serif;margin:32px;color:#111}}
table{{border-collapse:collapse;width:100%;margin:16px 0}}
td,th{{border:1px solid #ccc;padding:6px;vertical-align:top;font-size:12px}}
th{{background:#eee}}
code{{font-size:10px;word-break:break-all}}
.warn{{background:#fff3cd;padding:10px;border:1px solid #ffe69c}}
h1,h2{{page-break-after:avoid}}
</style></head><body>
<h1>Service-of-Process OSINT Packet</h1>
<div class='warn'><b>Use note:</b> public/lawfully obtained records only. Verify identity before relying on an address.</div>
<h2>{esc(defendant.name)}</h2><p><b>Role:</b> {esc(defendant.role)}<br><b>Type:</b> {esc(defendant.entity_type)}<br><b>Notes:</b> {esc(defendant.notes)}</p>
<h2>Aliases</h2><p>{esc(', '.join(p['aliases']))}</p>
<h2>Candidate Addresses</h2><table><tr><th>ID</th><th>Score</th><th>Address</th><th>City/State</th><th>Source</th><th>Last Seen</th><th>Tags</th><th>Notes</th></tr>{rows}</table>
<h2>Evidence</h2><table><tr><th>ID</th><th>Source</th><th>URL</th><th>Captured</th><th>File</th><th>SHA-256</th><th>Notes</th></tr>{evrows}</table>
<h2>Auto-Extracted Leads (unverified)</h2><table><tr><th>ID</th><th>Type</th><th>Value</th><th>Conf</th><th>Source</th><th>Verified</th></tr>{leadrows}</table>
<h2>Service Attempts / Due Diligence Log</h2><table><tr><th>ID</th><th>Address ID</th><th>Attempted At</th><th>Result</th><th>Notes</th></tr>{atrows}</table>
</body></html>"""


def write_html_packet(defendant: Defendant, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html_packet(defendant), encoding="utf-8")


def write_pdf_packet(defendant: Defendant, out: Path) -> None:
    from playwright.sync_api import sync_playwright

    out.parent.mkdir(parents=True, exist_ok=True)
    html_doc = render_html_packet(defendant)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_doc, wait_until="domcontentloaded")
        page.pdf(path=str(out), format="Letter", print_background=True)
        browser.close()


def write_full_packet(defendant: Defendant, out_dir: Path, formats: set[str] | None = None) -> dict[str, Path]:
    """Write HTML, JSON, CSV, and/or PDF packet files for a subject."""
    from service_osint.utils import slugify

    fmts = formats or {"html", "json", "csv", "pdf"}
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(defendant.name)
    written: dict[str, Path] = {}
    if "json" in fmts:
        path = out_dir / f"{slug}-packet.json"
        write_json(defendant, path)
        written["json"] = path
    if "csv" in fmts:
        path = out_dir / f"{slug}-addresses.csv"
        write_addresses_csv(defendant, path)
        written["csv"] = path
    if "html" in fmts:
        path = out_dir / f"{slug}-packet.html"
        write_html_packet(defendant, path)
        written["html"] = path
    if "pdf" in fmts:
        path = out_dir / f"{slug}-packet.pdf"
        write_pdf_packet(defendant, path)
        written["pdf"] = path
    return written
