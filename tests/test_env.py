from __future__ import annotations

import os

from service_osint.core.env import env_summary, find_env_file, load_env


def test_env_summary_masks_secrets(monkeypatch) -> None:
    monkeypatch.setenv("SERPER_API_KEY", "secret-key-value")
    monkeypatch.setenv("SEARXNG_URL", "http://127.0.0.1:8080")
    summary = env_summary()
    assert summary["SERPER_API_KEY"] == "(set)"
    assert summary["SEARXNG_URL"] == "http://127.0.0.1:8080"
    assert "secret" not in str(summary.values())


def test_load_env_does_not_crash(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SEARXNG_URL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("SEARXNG_URL=http://localhost:9999\n", encoding="utf-8")
    path = load_env()
    assert path == env_file
    assert os.getenv("SEARXNG_URL") == "http://localhost:9999"


def test_find_env_file_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert find_env_file() is None
