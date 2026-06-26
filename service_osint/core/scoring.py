from __future__ import annotations

TRUST_WEIGHTS = {
    "secretary of state": 20,
    "sos": 20,
    "sec": 20,
    "county recorder": 18,
    "county assessor": 18,
    "voter": 16,
    "court": 15,
    "ucc": 15,
    "process server": 25,
    "people search": 5,
    "social": 8,
    "discovery": 6,
}


def score_address(
    base_confidence: int,
    source: str,
    corroborations: int = 0,
    has_recent_date: bool = False,
) -> int:
    score = max(0, min(100, base_confidence))
    src = source.lower()
    score += max((w for k, w in TRUST_WEIGHTS.items() if k in src), default=0)
    score += min(corroborations, 5) * 7
    if has_recent_date:
        score += 10
    return max(0, min(100, score))
