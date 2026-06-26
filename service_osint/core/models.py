from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Defendant(Base):
    __tablename__ = "defendants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50), default="person")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    aliases: Mapped[list["Alias"]] = relationship(back_populates="defendant", cascade="all, delete-orphan")
    addresses: Mapped[list["Address"]] = relationship(back_populates="defendant", cascade="all, delete-orphan")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="defendant", cascade="all, delete-orphan")
    attempts: Mapped[list["ServiceAttempt"]] = relationship(back_populates="defendant", cascade="all, delete-orphan")
    leads: Mapped[list["Lead"]] = relationship(back_populates="defendant", cascade="all, delete-orphan")
    automation_runs: Mapped[list["AutomationRun"]] = relationship(back_populates="defendant", cascade="all, delete-orphan")


class Alias(Base):
    __tablename__ = "aliases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    defendant_id: Mapped[int] = mapped_column(ForeignKey("defendants.id"), index=True)
    alias: Mapped[str] = mapped_column(String(255), index=True)
    defendant: Mapped[Defendant] = relationship(back_populates="aliases")


class Address(Base):
    __tablename__ = "addresses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    defendant_id: Mapped[int] = mapped_column(ForeignKey("defendants.id"), index=True)
    address: Mapped[str] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(30), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    source: Mapped[str] = mapped_column(String(255))
    confidence: Mapped[int] = mapped_column(Integer, default=50)
    last_seen: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    defendant: Mapped[Defendant] = relationship(back_populates="addresses")


class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    defendant_id: Mapped[int] = mapped_column(ForeignKey("defendants.id"), index=True)
    source_name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(Text)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    defendant: Mapped[Defendant] = relationship(back_populates="evidence")


class ServiceAttempt(Base):
    __tablename__ = "service_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    defendant_id: Mapped[int] = mapped_column(ForeignKey("defendants.id"), index=True)
    address_id: Mapped[int | None] = mapped_column(ForeignKey("addresses.id"), nullable=True)
    attempted_at: Mapped[str] = mapped_column(String(50))
    result: Mapped[str] = mapped_column(String(500))
    server_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    defendant: Mapped[Defendant] = relationship(back_populates="attempts")
    address: Mapped[Address | None] = relationship()


class SourceBookmark(Base):
    __tablename__ = "source_bookmarks"
    __table_args__ = (UniqueConstraint("name", "url", name="uq_bookmark_name_url"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(80), nullable=True)
    url: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CollectionRun(Base):
    __tablename__ = "collection_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    defendant_id: Mapped[int] = mapped_column(ForeignKey("defendants.id"), index=True)
    collector: Mapped[str] = mapped_column(String(80), index=True)
    query: Mapped[str] = mapped_column(String(500))
    target_url: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="manual")
    evidence_id: Mapped[int | None] = mapped_column(ForeignKey("evidence.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    defendant: Mapped[Defendant] = relationship()
    evidence: Mapped[Evidence | None] = relationship()


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (UniqueConstraint("defendant_id", "lead_type", "value", name="uq_lead_subject_type_value"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    defendant_id: Mapped[int] = mapped_column(ForeignKey("defendants.id"), index=True)
    lead_type: Mapped[str] = mapped_column(String(40), index=True)
    value: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(255))
    confidence: Mapped[int] = mapped_column(Integer, default=10)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    defendant: Mapped[Defendant] = relationship(back_populates="leads")


class AutomationRun(Base):
    __tablename__ = "automation_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    defendant_id: Mapped[int] = mapped_column(ForeignKey("defendants.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="running")
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    defendant: Mapped[Defendant] = relationship(back_populates="automation_runs")
