"""Severity-level filtering and ordering for log lines."""

import re
from typing import Iterable, Iterator, List, Optional

# Ordered from lowest to highest severity
LEVELS: List[str] = ["debug", "info", "notice", "warn", "warning", "error", "err", "crit", "fatal"]

# Canonical mapping (aliases -> canonical)
_CANONICAL = {
    "debug": "debug",
    "info": "info",
    "notice": "notice",
    "warn": "warn",
    "warning": "warn",
    "error": "error",
    "err": "error",
    "crit": "crit",
    "fatal": "fatal",
}

# Severity rank (canonical name -> int)
_RANK = {
    "debug": 0,
    "info": 1,
    "notice": 2,
    "warn": 3,
    "error": 4,
    "crit": 5,
    "fatal": 6,
}

_LEVEL_RE = re.compile(
    r"\b(debug|info|notice|warn(?:ing)?|err(?:or)?|crit(?:ical)?|fatal)\b",
    re.IGNORECASE,
)


def parse_level(level: str) -> str:
    """Return the canonical level name, or raise ValueError if unknown."""
    key = level.strip().lower()
    if key not in _CANONICAL:
        raise ValueError(f"Unknown severity level: {level!r}")
    return _CANONICAL[key]


def level_rank(level: str) -> int:
    """Return the numeric rank for a canonical level name."""
    canonical = parse_level(level)
    return _RANK[canonical]


def extract_level(line: str) -> Optional[str]:
    """Return the first severity level found in *line*, or None."""
    m = _LEVEL_RE.search(line)
    if m is None:
        return None
    return _CANONICAL[m.group(0).lower()]


def filter_by_severity(
    lines: Iterable[str],
    min_level: str,
    max_level: Optional[str] = None,
) -> Iterator[str]:
    """Yield lines whose detected severity falls within [min_level, max_level]."""
    min_rank = level_rank(min_level)
    max_rank = level_rank(max_level) if max_level is not None else max(_RANK.values())
    for line in lines:
        lvl = extract_level(line)
        if lvl is None:
            continue
        rank = _RANK[lvl]
        if min_rank <= rank <= max_rank:
            yield line
