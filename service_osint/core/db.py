from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from service_osint.core.errors import DatabaseError

APP_DIR = Path.home() / ".service-osint"
DB_PATH = APP_DIR / "case.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def ensure_app_dirs() -> None:
    """Create application data directories if missing."""
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        (APP_DIR / "captures").mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DatabaseError(
            f"Cannot create app directory {APP_DIR}: {exc}",
            hint="Check home directory permissions.",
        ) from exc


def init_db() -> None:
    """Create tables; raises DatabaseError on failure."""
    ensure_app_dirs()
    try:
        from . import models  # noqa: F401

        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as exc:
        raise DatabaseError(
            f"Failed to initialize database at {DB_PATH}: {exc}",
            hint="Run `osint doctor` or delete a corrupted case.db after backup.",
        ) from exc


def verify_db_connection() -> bool:
    """Return True if the database accepts queries."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


def table_names() -> list[str]:
    return inspect(engine).get_table_names()
