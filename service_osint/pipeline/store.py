from __future__ import annotations

import json
from sqlalchemy import select

from service_osint.core.models import AutomationRun, Defendant, Evidence, Lead, utcnow
from service_osint.discovery.base import SearchHit
from service_osint.pipeline.types import PipelineResult


def ensure_subject(
    session,
    config,
) -> Defendant:
    obj = session.scalar(select(Defendant).where(Defendant.name == config.subject))
    if obj:
        if config.role and not obj.role:
            obj.role = config.role
        if config.entity_type and obj.entity_type != config.entity_type:
            obj.entity_type = config.entity_type
        session.commit()
        return obj
    obj = Defendant(
        name=config.subject,
        role=config.role,
        entity_type=config.entity_type,
        notes="Created by OSINT automation pipeline",
    )
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def evidence_exists(session, defendant_id: int, url: str) -> bool:
    return bool(
        session.scalar(
            select(Evidence.id).where(
                Evidence.defendant_id == defendant_id,
                Evidence.url == url,
            )
        )
    )


def add_evidence_url(
    session,
    defendant_id: int,
    source: str,
    url: str,
    notes: str | None = None,
    file_path: str | None = None,
    sha256: str | None = None,
) -> int | None:
    if evidence_exists(session, defendant_id, url):
        return None
    ev = Evidence(
        defendant_id=defendant_id,
        source_name=source,
        url=url,
        notes=notes,
        file_path=file_path,
        sha256=sha256,
    )
    session.add(ev)
    session.flush()
    return ev.id


def persist_discovery_hits(
    session,
    defendant_id: int,
    hits: list[SearchHit],
    query: str,
) -> int:
    added = 0
    for hit in hits:
        if not hit.url:
            continue
        notes = f"Query: {query}\n{hit.snippet}" if hit.snippet else f"Query: {query}"
        if add_evidence_url(session, defendant_id, f"auto/discovery/{hit.provider}", hit.url, notes=notes):
            added += 1
    session.commit()
    return added


def persist_dork_seeds(session, defendant_id: int, dorks, url_fn) -> int:
    added = 0
    for d in dorks:
        url = url_fn(d.query)
        note = f"Dork [{d.label}]: {d.query}\n{d.purpose}"
        if add_evidence_url(session, defendant_id, "auto/dork", url, notes=note):
            added += 1
    session.commit()
    return added


def lead_exists(session, defendant_id: int, lead_type: str, value: str) -> bool:
    return bool(
        session.scalar(
            select(Lead.id).where(
                Lead.defendant_id == defendant_id,
                Lead.lead_type == lead_type,
                Lead.value == value,
            )
        )
    )


def persist_leads(session, defendant_id: int, lead_map: dict[str, set[str]], source: str) -> int:
    added = 0
    confidence = {"phone": 25, "email": 30, "address": 15, "zip": 10, "social": 35, "url": 20}
    for lead_type, values in lead_map.items():
        for value in values:
            if len(value) < 5 and lead_type == "address":
                continue
            stored = value[:500]
            if lead_exists(session, defendant_id, lead_type, stored):
                continue
            session.add(
                Lead(
                    defendant_id=defendant_id,
                    lead_type=lead_type,
                    value=stored,
                    source=source,
                    confidence=confidence.get(lead_type, 10),
                    verified=False,
                )
            )
            added += 1
    session.commit()
    return added


def start_automation_run(session, defendant_id: int, config) -> AutomationRun:
    run = AutomationRun(
        defendant_id=defendant_id,
        status="running",
        config_json=json.dumps(
            {
                "subject": config.subject,
                "entity_type": config.entity_type,
                "city": config.city,
                "state": config.state,
            },
            ensure_ascii=False,
        ),
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def finish_automation_run(session, run: AutomationRun, result: PipelineResult) -> None:
    run.status = "completed" if result.ok else "completed_with_errors"
    run.finished_at = utcnow()
    run.summary_json = json.dumps(
        {
            "evidence_added": result.evidence_added,
            "leads_added": result.leads_added,
            "collectors_run": result.collectors_run,
            "discovery_hits": result.discovery_hits,
            "steps": [{"step": s.step, "status": s.status, "detail": s.detail, "count": s.count} for s in result.steps],
            "packet": {k: str(v) for k, v in result.packet_paths.items()},
        },
        ensure_ascii=False,
        indent=2,
    )
    session.commit()
