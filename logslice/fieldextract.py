"""Field extraction from structured log lines (key=value, JSON-like pairs)."""

import re
from typing import Dict, Optional

# Matches key=value or key="value with spaces"
_KV_PATTERN = re.compile(
    r'(?P<key>[\w.\-]+)=(?P<value>"[^"]*"|\S+)'
)

# Matches simple JSON string fields: "key": "value" or "key": number
_JSON_FIELD_PATTERN = re.compile(
    r'"(?P<key>[^"]+)"\s*:\s*(?P<value>"[^"]*"|[\d.]+|true|false|null)'
)


def extract_fields(line: str) -> Dict[str, str]:
    """Extract key=value pairs from a log line.

    Tries key=value format first; falls back to JSON field extraction.
    Returns a dict of field names to string values (quotes stripped).
    """
    fields: Dict[str, str] = {}

    kv_matches = _KV_PATTERN.findall(line)
    if kv_matches:
        for key, value in kv_matches:
            fields[key] = value.strip('"')
        return fields

    json_matches = _JSON_FIELD_PATTERN.findall(line)
    for key, value in json_matches:
        fields[key] = value.strip('"')

    return fields


def get_field(line: str, field: str) -> Optional[str]:
    """Return the value of a single named field from a log line, or None."""
    return extract_fields(line).get(field)


def filter_by_field(lines, field: str, value: str):
    """Yield only lines where the extracted field equals the given value."""
    for line in lines:
        if get_field(line, field) == value:
            yield line


def field_values(lines, field: str):
    """Yield the value of *field* for each line that contains it."""
    for line in lines:
        val = get_field(line, field)
        if val is not None:
            yield val
