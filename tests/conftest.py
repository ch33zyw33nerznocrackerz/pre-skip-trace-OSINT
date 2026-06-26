from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Use a temporary SQLite database for tests."""
    app_dir = tmp_path / "service-osint"
    app_dir.mkdir()
    db_path = app_dir / "case.db"

    test_engine = create_engine(f"sqlite:///{db_path}", echo=False, future=True)
    test_session = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

    monkeypatch.setattr("service_osint.core.db.APP_DIR", app_dir)
    monkeypatch.setattr("service_osint.core.db.DB_PATH", db_path)
    monkeypatch.setattr("service_osint.core.db.engine", test_engine)
    monkeypatch.setattr("service_osint.core.db.SessionLocal", test_session)

    from service_osint.core.db import init_db

    init_db()
    return db_path
