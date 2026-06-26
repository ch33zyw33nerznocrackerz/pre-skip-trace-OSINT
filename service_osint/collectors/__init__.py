from __future__ import annotations

from service_osint.collectors.base import CollectResult, Collector
from service_osint.collectors.court import CourtCollector
from service_osint.collectors.opencorp import OpenCorpCollector
from service_osint.collectors.people import PeopleCollector
from service_osint.collectors.nvsos import NvsosCollector
from service_osint.collectors.property import PropertyCollector
from service_osint.collectors.sec import SecCollector
from service_osint.collectors.socials import SocialsCollector

COLLECTORS: dict[str, Collector] = {
    "sec": SecCollector(),
    "nvsos": NvsosCollector(),
    "opencorp": OpenCorpCollector(),
    "property": PropertyCollector(),
    "court": CourtCollector(),
    "socials": SocialsCollector(),
    "people": PeopleCollector(),
}


def list_collectors() -> list[tuple[str, str]]:
    return [(name, c.label) for name, c in COLLECTORS.items()]


def run_collector(
    collector_name: str,
    subject: str,
    *,
    capture: bool = True,
    wait_ms: int = 2000,
    state: str | None = None,
    city: str | None = None,
) -> CollectResult:
    key = collector_name.lower()
    collector = COLLECTORS.get(key)
    if not collector:
        known = ", ".join(sorted(COLLECTORS))
        raise ValueError(f"Unknown collector {collector_name!r}. Choose: {known}")
    return collector.collect(subject, capture=capture, wait_ms=wait_ms, state=state, city=city)


def persist_collection(
    session,
    defendant_id: int,
    result: CollectResult,
) -> tuple[int, int]:
    """Save evidence + collection run; returns (evidence_id, run_id)."""
    from service_osint.core.models import CollectionRun, Evidence

    source = f"collector/{result.collector}"
    notes_parts = [result.notes]
    if result.manual_steps:
        notes_parts.append("Manual: " + " | ".join(result.manual_steps[:2]))
    evidence = Evidence(
        defendant_id=defendant_id,
        source_name=source,
        url=result.url,
        notes="\n".join(notes_parts),
        file_path=str(result.screenshot_path) if result.screenshot_path else None,
        sha256=result.sha256,
    )
    session.add(evidence)
    session.flush()

    run = CollectionRun(
        defendant_id=defendant_id,
        collector=result.collector,
        query=result.subject,
        target_url=result.url,
        status="captured" if result.screenshot_path else "manual",
        evidence_id=evidence.id,
        notes=result.notes,
    )
    session.add(run)
    session.commit()
    return evidence.id, run.id
