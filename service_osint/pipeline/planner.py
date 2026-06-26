from __future__ import annotations

from service_osint.pipeline.types import PipelineConfig


def default_collectors(config: PipelineConfig) -> list[str]:
    if config.collectors:
        return list(config.collectors)
    if config.entity_type == "company":
        return ["sec", "opencorp", "nvsos"]
    cols = ["property", "court", "socials", "people"]
    name_lower = config.subject.lower()
    if "," in config.subject or "inc" in name_lower or "llc" in name_lower:
        cols = ["nvsos", "opencorp", *cols]
    return cols


def plan_steps(config: PipelineConfig) -> list[str]:
    steps = ["subject", "dorks_seed"]
    if config.discovery:
        steps.append("discovery_person")
        if config.dork_discovery:
            steps.append("discovery_dorks")
    steps.extend(f"collect:{c}" for c in default_collectors(config))
    if config.foss:
        steps.append("foss_tools")
    if config.domain_recon:
        steps.append("domain_recon")
    if config.social_pai:
        steps.append("social_pai")
    steps.extend(["jina_enrich", "extract_leads", "serve_plan"])
    if config.export_packet:
        steps.append("export_packet")
    return steps


def person_discovery_query(config: PipelineConfig) -> str:
    parts = [f'"{config.subject}"']
    if config.city:
        parts.append(config.city)
    if config.state:
        parts.append(config.state)
    parts.append("(address OR phone OR residence OR contact OR obituary OR court)")
    return " ".join(parts)
