"""Label-based filtering for structured log lines with key=value pairs."""

import re
from typing import Iterable, Iterator, Optional

_KV_RE = re.compile(r'(\w[\w.\-]*)\s*=\s*(?:"([^"]*)"|(\'[^\']*\')|([\S]*))')


def parse_labels(line: str) -> dict:
    """Extract all key=value labels from a log line."""
    result = {}
    for m in _KV_RE.finditer(line):
        key = m.group(1)
        value = m.group(2) or m.group(3) or m.group(4) or ""
        if m.group(3):
            value = value.strip("'")
        result[key] = value
    return result


def label_matches(labels: dict, key: str, value: Optional[str] = None,
                  negate: bool = False) -> bool:
    """Check whether a label dict satisfies a key[=value] condition."""
    if key not in labels:
        return negate
    if value is None:
        result = True
    else:
        result = labels[key] == value
    return (not result) if negate else result


def parse_label_expr(expr: str):
    """Parse a label expression like 'key=value', 'key', or '!key=value'.

    Returns (negate, key, value_or_None).
    """
    negate = False
    if expr.startswith("!"):
        negate = True
        expr = expr[1:]
    if "=" in expr:
        key, _, value = expr.partition("=")
        return negate, key.strip(), value.strip()
    return negate, expr.strip(), None


def filter_by_labels(
    lines: Iterable[str],
    expressions: list,
) -> Iterator[str]:
    """Yield lines that satisfy ALL label expressions.

    Each expression is a string like 'level=error', 'host', or '!env=prod'.
    """
    parsed = [parse_label_expr(e) for e in expressions]
    for line in lines:
        labels = parse_labels(line)
        if all(label_matches(labels, key, val, neg) for neg, key, val in parsed):
            yield line
