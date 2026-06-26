from __future__ import annotations

import json
from pathlib import Path

from service_osint.domain.parse import parse_live_hosts, parse_subdomains, parse_tls_names, recon_lead_map
from service_osint.domain.utils import (
    domain_from_email,
    domain_from_employer,
    is_free_email_domain,
    normalize_domain,
    resolve_scan_domain,
)


def test_normalize_domain() -> None:
    assert normalize_domain("https://www.AcmeCorp.com/about") == "acmecorp.com"
    assert normalize_domain("invalid domain") is None


def test_free_email_filtered() -> None:
    assert is_free_email_domain("gmail.com")
    assert domain_from_email("jane@gmail.com") is None
    assert domain_from_email("jane@acmecorp.com") == "acmecorp.com"


def test_resolve_scan_domain_priority() -> None:
    assert resolve_scan_domain(domain="explicit.com", email="a@b.com") == "explicit.com"
    assert resolve_scan_domain(email="jane@acmecorp.com") == "acmecorp.com"
    assert resolve_scan_domain(employer="legacy.acmecorp.com") == "legacy.acmecorp.com"
    assert resolve_scan_domain(email="jane@gmail.com") is None


def test_parse_live_hosts_jsonl(tmp_path: Path) -> None:
    live = tmp_path / "live.json"
    live.write_text(
        json.dumps({"url": "https://mail.acme.com", "title": "Webmail", "status_code": 200}) + "\n",
        encoding="utf-8",
    )
    rows = parse_live_hosts(tmp_path)
    assert len(rows) == 1
    assert rows[0]["url"] == "https://mail.acme.com"


def test_recon_lead_map(tmp_path: Path) -> None:
    (tmp_path / "subs.txt").write_text("portal.acme.com\n", encoding="utf-8")
    leads = recon_lead_map(tmp_path)
    assert "https://portal.acme.com" in leads["url"]


def test_parse_subdomains_and_tls(tmp_path: Path) -> None:
    (tmp_path / "resolved.txt").write_text("api.acme.com\n", encoding="utf-8")
    assert "api.acme.com" in parse_subdomains(tmp_path)
    (tmp_path / "tls.json").write_text(
        json.dumps({"subject_cn": "acme.com", "san": ["*.acme.com"]}) + "\n",
        encoding="utf-8",
    )
    assert "acme.com" in parse_tls_names(tmp_path)
