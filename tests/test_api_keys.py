from __future__ import annotations

from service_osint.core.api_keys import (
    API_KEY_SPECS,
    configured_keys,
    missing_keys,
)


def test_missing_keys_when_empty(monkeypatch) -> None:
    for spec in API_KEY_SPECS:
        monkeypatch.delenv(spec.env_var, raising=False)
    assert len(missing_keys()) == len(API_KEY_SPECS)
    assert configured_keys() == []


def test_configured_serper(monkeypatch) -> None:
    monkeypatch.setenv("SERPER_API_KEY", "test-key")
    configured = {s.env_var for s in configured_keys()}
    assert "SERPER_API_KEY" in configured
    missing = {s.env_var for s in missing_keys()}
    assert "SERPER_API_KEY" not in missing


def test_tier_labels() -> None:
    spec = next(s for s in API_KEY_SPECS if s.env_var == "SERPER_API_KEY")
    assert spec.tier == "freemium"
    assert "FREE" in spec.tier_label()
    paid = next(s for s in API_KEY_SPECS if s.env_var == "LINKUP_API_KEY")
    assert paid.tier == "paid"
