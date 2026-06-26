from __future__ import annotations

import time
from service_osint.collectors import persist_collection, run_collector
from service_osint.core.db import SessionLocal
from service_osint.discovery import discover
from service_osint.domain import resolve_scan_domain, run_domain_recon
from service_osint.export import write_full_packet
from service_osint.pipeline.extract import extract_leads, merge_lead_maps
from service_osint.pipeline.jina import enrich_urls_with_jina
from service_osint.pipeline.planner import default_collectors, person_discovery_query, plan_steps
from service_osint.pipeline.store import (
    add_evidence_url,
    ensure_subject,
    finish_automation_run,
    persist_discovery_hits,
    persist_dork_seeds,
    persist_leads,
    start_automation_run,
)
from service_osint.foss import FossTarget, foss_tools_for_target, run_foss_tool
from service_osint.social import run_social_pai
from service_osint.pipeline.types import PipelineConfig, PipelineResult, StepResult
from service_osint.sources.dorks import google_search_url, person_dorks


def run_pipeline(config: PipelineConfig, on_step=None) -> PipelineResult:
    """Execute full OSINT automation for a subject."""
    result = PipelineResult(subject=config.subject, defendant_id=0)

    def emit(step: str, status: str, detail: str = "", count: int = 0, duration_ms: float = 0.0) -> None:
        sr = StepResult(step=step, status=status, detail=detail, count=count, duration_ms=duration_ms)
        result.steps.append(sr)
        if on_step:
            on_step(sr)

    def timed_step(step_name: str, fn):
        """Execute a function and emit timing information."""
        start_time = time.perf_counter()
        try:
            return fn()
        finally:
            duration = (time.perf_counter() - start_time) * 1000
            # Update the last step result with timing if it matches
            if result.steps and result.steps[-1].step == step_name:
                result.steps[-1].duration_ms = round(duration, 1)

    with SessionLocal() as s:
        defendant = ensure_subject(s, config)
        result.defendant_id = defendant.id
        emit("subject", "ok", f"Subject id={defendant.id}")

        auto_run = start_automation_run(s, defendant.id, config)
        result.automation_run_id = auto_run.id

        # --- Dork seed URLs ---
        try:
            dorks = person_dorks(
                config.subject,
                city=config.city,
                state=config.state,
                phone=config.phone,
                email=config.email,
                employer=config.employer,
            )
            n = persist_dork_seeds(s, defendant.id, dorks, google_search_url)
            result.evidence_added += n
            emit("dorks_seed", "ok", f"{len(dorks)} dorks, {n} new URLs", n)
        except (ValueError, TypeError, KeyError) as exc:
            emit("dorks_seed", "error", f"Configuration error: {exc}")
        except Exception as exc:
            emit("dorks_seed", "error", f"Unexpected error: {exc}")

        all_text: list[str] = []
        hit_urls: list[str] = []

        # --- Discovery: person query ---
        if config.discovery:
            try:
                q = person_discovery_query(config)
                blocks = discover(q, limit=config.discovery_limit)
                hits = []
                for block in blocks:
                    if block.error:
                        emit(f"discovery:{block.provider}", "skipped", block.error)
                        continue
                    hits.extend(block.hits)
                    all_text.extend(h.snippet for h in block.hits if h.snippet)
                    hit_urls.extend(h.url for h in block.hits if h.url)
                n = persist_discovery_hits(s, defendant.id, hits, q)
                result.discovery_hits += len(hits)
                result.evidence_added += n
                emit("discovery_person", "ok", f"{len(hits)} hits, {n} new evidence", n)
            except (ValueError, TypeError, KeyError) as exc:
                emit("discovery_person", "error", f"Configuration error: {exc}")
            except Exception as exc:
                emit("discovery_person", "error", f"Unexpected error: {exc}")

            # --- Discovery: top dork queries ---
            if config.dork_discovery:
                try:
                    top = person_dorks(config.subject, city=config.city, state=config.state)[: config.dork_limit]
                    dork_hits = []
                    for d in top:
                        blocks = discover(d.query, limit=4)
                        for block in blocks:
                            if not block.error:
                                dork_hits.extend(block.hits)
                                all_text.extend(h.snippet for h in block.hits if h.snippet)
                                hit_urls.extend(h.url for h in block.hits if h.url)
                    n = persist_discovery_hits(
                        s,
                        defendant.id,
                        dork_hits,
                        "dork-batch",
                    )
                    result.discovery_hits += len(dork_hits)
                    result.evidence_added += n
                    emit("discovery_dorks", "ok", f"{len(dork_hits)} hits from {len(top)} dorks", n)
                except (ValueError, TypeError, KeyError) as exc:
                    emit("discovery_dorks", "error", f"Configuration error: {exc}")
                except Exception as exc:
                    emit("discovery_dorks", "error", f"Unexpected error: {exc}")

        # --- Collectors ---
        for coll in default_collectors(config):
            step = f"collect:{coll}"
            try:
                cr = run_collector(
                    coll,
                    config.subject,
                    capture=config.capture,
                    wait_ms=config.wait_ms,
                    state=config.state,
                    city=config.city,
                )
                eid, _ = persist_collection(s, defendant.id, cr)
                result.collectors_run += 1
                result.evidence_added += 1
                for u in cr.extra_urls:
                    if add_evidence_url(s, defendant.id, f"auto/collector/{coll}", u, notes=cr.notes):
                        result.evidence_added += 1
                emit(step, "ok", f"evidence #{eid}", 1)
            except (ValueError, TypeError, KeyError) as exc:
                emit(step, "error", f"Configuration error: {exc}")
            except Exception as exc:
                emit(step, "error", f"Unexpected error: {exc}")

        # --- FOSS: SpiderFoot / Photon (optional, slow) ---
        if config.foss:
            scan_domain = resolve_scan_domain(
                domain=config.domain,
                email=config.email,
                employer=config.employer,
            )
            foss_target = FossTarget(
                email=config.email,
                domain=scan_domain,
                url=hit_urls[0] if hit_urls else None,
            )
            tool_ids = foss_tools_for_target(foss_target)
            foss_ran = 0
            for tool_id in tool_ids:
                try:
                    out_dir = config.out_dir / "foss" / tool_id.replace("/", "_")
                    foss_result = run_foss_tool(tool_id, foss_target, output_dir=out_dir)
                    if foss_result.get("success"):
                        foss_ran += 1
                        summary = (foss_result.get("stdout") or "")[:2000]
                        add_evidence_url(
                            s,
                            defendant.id,
                            f"foss/{tool_id}",
                            f"file://{out_dir.resolve()}",
                            notes=summary or f"FOSS run: {tool_id}",
                        )
                        result.evidence_added += 1
                        all_text.append(summary)
                    else:
                        emit(f"foss:{tool_id}", "skipped", foss_result.get("error", "failed")[:80])
                except (ValueError, TypeError, KeyError) as exc:
                    emit(f"foss:{tool_id}", "error", f"Configuration error: {exc}")
                except Exception as exc:
                    emit(f"foss:{tool_id}", "error", f"Unexpected error: {exc}")
            if foss_ran:
                emit("foss_tools", "ok", f"{foss_ran}/{len(tool_ids)} tools completed", foss_ran)
            elif tool_ids:
                emit("foss_tools", "skipped", "no tools succeeded (check FOSS_DOCKER or SPIDERFOOT_DIR)")
            else:
                emit("foss_tools", "skipped", "no email/domain/url seed for FOSS tools")

        # --- Domain recon: subfinder → dnsx → httpx → tlsx ---
        if config.domain_recon:
            scan_domain = resolve_scan_domain(
                domain=config.domain,
                email=config.email,
                employer=config.employer,
            )
            if not scan_domain:
                emit("domain_recon", "skipped", "no corporate domain (gmail/yahoo or missing email)")
            else:
                try:
                    out_dir = config.out_dir / "domain" / scan_domain.replace(".", "_")
                    recon = run_domain_recon(domain=scan_domain, output_dir=out_dir)
                    added = 0
                    for row in recon.live_hosts:
                        note = f"Domain recon — {row.get('title') or ''}".strip()
                        if add_evidence_url(
                            s,
                            defendant.id,
                            "domain-recon/httpx",
                            row["url"],
                            notes=note or f"Live host on {scan_domain}",
                        ):
                            added += 1
                            hit_urls.append(row["url"])
                    for host in recon.subdomains:
                        url = f"https://{host}"
                        if add_evidence_url(
                            s,
                            defendant.id,
                            "domain-recon/subdomain",
                            url,
                            notes=f"Subdomain of {scan_domain}",
                        ):
                            added += 1
                    result.leads_added += persist_leads(s, defendant.id, recon.lead_map, "domain-recon")
                    result.evidence_added += added
                    detail = (
                        f"{len(recon.subdomains)} subs, {len(recon.live_hosts)} live, "
                        f"{recon.tools_run} tools"
                    )
                    status = "ok" if recon.tools_run else "skipped"
                    emit("domain_recon", status, detail, added)
                    if recon.errors:
                        emit("domain_recon_notes", "skipped", "; ".join(recon.errors[:2]))
                except (ValueError, TypeError, KeyError) as exc:
                    emit("domain_recon", "error", f"Configuration error: {exc}")
                except Exception as exc:
                    emit("domain_recon", "error", f"Unexpected error: {exc}")

        # --- Social PAI: username / email / phone across platforms ---
        if config.social_pai:
            try:
                pai = run_social_pai(config, out_dir=config.out_dir / "social", full=False)
                for url in pai.profiles:
                    if add_evidence_url(s, defendant.id, "social/pai", url, notes="Automated social PAI"):
                        result.evidence_added += 1
                if pai.profiles:
                    result.leads_added += persist_leads(
                        s, defendant.id, {"social": pai.profiles}, "auto/social-pai"
                    )
                if pai.raw_text:
                    all_text.extend(pai.raw_text)
                detail = f"{len(pai.profiles)} profiles, {pai.tools_run} tools"
                emit("social_pai", "ok" if pai.profiles else "skipped", detail, len(pai.profiles))
            except (ValueError, TypeError, KeyError) as exc:
                emit("social_pai", "error", f"Configuration error: {exc}")
            except Exception as exc:
                emit("social_pai", "error", f"Unexpected error: {exc}")

        # --- Jina Reader: pull page text from top discovery URLs ---
        try:
            unique_urls: list[str] = []
            seen_u: set[str] = set()
            for u in hit_urls:
                key = u.split("#")[0].rstrip("/")
                if key.startswith("http") and key not in seen_u:
                    seen_u.add(key)
                    unique_urls.append(key)
            jina_chunks = enrich_urls_with_jina(unique_urls, limit=5)
            all_text.extend(jina_chunks)
            emit("jina_enrich", "ok", f"{len(jina_chunks)} pages fetched", len(jina_chunks))
        except (ValueError, TypeError, KeyError) as exc:
            emit("jina_enrich", "error", f"Configuration error: {exc}")
        except Exception as exc:
            emit("jina_enrich", "error", f"Unexpected error: {exc}")

        # --- Extract leads from discovery snippets + evidence notes ---
        try:
            s.refresh(defendant)
            for ev in defendant.evidence:
                if ev.notes:
                    all_text.append(ev.notes)
            merged = merge_lead_maps(extract_leads("\n".join(all_text)))
            if config.phone:
                merged["phone"].add(config.phone)
            if config.email:
                merged["email"].add(config.email.lower())
            n = persist_leads(s, defendant.id, merged, "auto/extract")
            result.leads_added = n
            emit(
                "extract_leads",
                "ok",
                f"phones={len(merged['phone'])} emails={len(merged['email'])} addresses={len(merged['address'])}",
                n,
            )
        except (ValueError, TypeError, KeyError) as exc:
            emit("extract_leads", "error", f"Configuration error: {exc}")
        except Exception as exc:
            emit("extract_leads", "error", f"Unexpected error: {exc}")

        emit("serve_plan", "ok", "Use: osint serve-plan " + config.subject)

        # --- Packet export ---
        if config.export_packet:
            try:
                s.refresh(defendant)
                result.packet_paths = write_full_packet(
                    defendant,
                    config.out_dir,
                    formats=config.packet_formats,
                )
                emit("export_packet", "ok", ", ".join(result.packet_paths.keys()), len(result.packet_paths))
            except (ValueError, TypeError, KeyError) as exc:
                emit("export_packet", "error", f"Configuration error: {exc}")
            except Exception as exc:
                emit("export_packet", "error", f"Unexpected error: {exc}")

        finish_automation_run(s, auto_run, result)

    return result


def preview_plan(config: PipelineConfig) -> list[str]:
    return plan_steps(config)
