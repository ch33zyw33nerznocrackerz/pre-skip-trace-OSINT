from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

EntityType = Literal["person", "organization", "business"]
StepStatus = Literal["ok", "skipped", "error"]
PacketFormat = Literal["html", "json", "csv", "pdf"]


@dataclass
class PipelineConfig:
    subject: str
    entity_type: EntityType = "person"
    city: str | None = None
    state: str | None = None
    phone: str | None = None
    email: str | None = None
    employer: str | None = None
    role: str | None = None
    aliases: list[str] | None = None
    capture: bool = True
    wait_ms: int = 2500
    discovery: bool = True
    discovery_limit: int = 6
    dork_discovery: bool = True
    dork_limit: int = 3
    collectors: list[str] | None = None
    export_packet: bool = True
    packet_formats: set[PacketFormat] = field(default_factory=lambda: {"html", "json", "csv", "pdf"})
    out_dir: Path = field(default_factory=lambda: Path("out"))
    foss: bool = False
    social_pai: bool = False
    domain: str | None = None
    domain_recon: bool = False

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.subject.strip():
            raise ValueError("Subject name cannot be empty")
        
        if self.wait_ms < 0:
            raise ValueError("wait_ms must be non-negative")
        
        if self.discovery_limit < 1 or self.discovery_limit > 50:
            raise ValueError("discovery_limit must be between 1 and 50")
        
        if self.dork_limit < 1 or self.dork_limit > 20:
            raise ValueError("dork_limit must be between 1 and 20")
        
        # Validate packet formats
        valid_formats = {"html", "json", "csv", "pdf"}
        invalid_formats = self.packet_formats - valid_formats
        if invalid_formats:
            raise ValueError(f"Invalid packet formats: {invalid_formats}")


@dataclass
class StepResult:
    step: str
    status: StepStatus
    detail: str = ""
    count: int = 0


@dataclass
class PipelineResult:
    subject: str
    defendant_id: int
    steps: list[StepResult] = field(default_factory=list)
    evidence_added: int = 0
    leads_added: int = 0
    collectors_run: int = 0
    discovery_hits: int = 0
    packet_paths: dict[str, Path] = field(default_factory=dict)
    automation_run_id: int | None = None

    @property
    def ok(self) -> bool:
        return not any(s.status == "error" for s in self.steps)
