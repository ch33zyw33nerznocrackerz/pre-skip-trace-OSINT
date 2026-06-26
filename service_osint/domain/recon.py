from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from service_osint.domain.parse import parse_live_hosts, parse_subdomains, parse_tls_names, recon_lead_map
from service_osint.domain.utils import resolve_scan_domain
from service_osint.foss import FossTarget, run_foss_tool

_DOMAIN_TOOL_CHAIN = ("subfinder", "dnsx", "httpx-pd", "tlsx")


@dataclass
class DomainReconResult:
    domain: str
    output_dir: Path
    subdomains: list[str] = field(default_factory=list)
    live_hosts: list[dict[str, str]] = field(default_factory=list)
    tls_names: list[str] = field(default_factory=list)
    tools_run: int = 0
    errors: list[str] = field(default_factory=list)
    skipped_reason: str = ""

    @property
    def lead_map(self) -> dict[str, set[str]]:
        return recon_lead_map(self.output_dir)

    @property
    def ok(self) -> bool:
        return bool(self.tools_run) and not self.skipped_reason


def _ensure_subs_file(output_dir: Path, domain: str) -> None:
    subs = output_dir / "subs.txt"
    if subs.is_file() and subs.stat().st_size > 0:
        return
    subs.write_text(f"{domain}\nwww.{domain}\n", encoding="utf-8")


def _ensure_resolved_file(output_dir: Path, domain: str) -> None:
    resolved = output_dir / "resolved.txt"
    if resolved.is_file() and resolved.stat().st_size > 0:
        return
    subs = parse_subdomains(output_dir)
    seeds = subs or [domain, f"www.{domain}"]
    resolved.write_text("\n".join(dict.fromkeys(seeds)) + "\n", encoding="utf-8")


def run_domain_recon(
    *,
    domain: str | None = None,
    email: str | None = None,
    employer: str | None = None,
    output_dir: Path | None = None,
    include_tls: bool = True,
    dry_run: bool = False,
) -> DomainReconResult:
    """Run subfinder → dnsx → httpx → tlsx for a corporate/owned domain."""
    resolved = resolve_scan_domain(domain=domain, email=email, employer=employer)
    if not resolved:
        return DomainReconResult(
            domain="",
            output_dir=output_dir or Path("out/domain"),
            skipped_reason="No scannable domain — set --domain or use a non-free email domain.",
        )

    out = output_dir or Path("out") / "domain" / resolved.replace(".", "_")
    out.mkdir(parents=True, exist_ok=True)
    target = FossTarget(domain=resolved)
    result = DomainReconResult(domain=resolved, output_dir=out)

    tools = [t for t in _DOMAIN_TOOL_CHAIN if include_tls or t != "tlsx"]
    for tool_id in tools:
        if tool_id == "dnsx":
            _ensure_subs_file(out, resolved)
        if tool_id in {"httpx-pd", "tlsx"}:
            _ensure_resolved_file(out, resolved)

        foss = run_foss_tool(tool_id, target, output_dir=out, dry_run=dry_run)
        if foss.get("dry_run"):
            result.tools_run += 1
            continue
        if foss.get("success"):
            result.tools_run += 1
        else:
            err = foss.get("error") or foss.get("stderr", "")[:200] or f"{tool_id} failed"
            result.errors.append(f"{tool_id}: {err}")

    result.subdomains = parse_subdomains(out)
    result.live_hosts = parse_live_hosts(out)
    result.tls_names = parse_tls_names(out)
    return result
