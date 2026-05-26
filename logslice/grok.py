"""Grok-style named pattern matching for structured log parsing."""

import re
from typing import Dict, List, Optional

# Built-in named patterns
BUILTIN_PATTERNS: Dict[str, str] = {
    "INT": r"[+-]?(?:[0-9]+)",
    "FLOAT": r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)",
    "WORD": r"\b\w+\b",
    "NOTSPACE": r"\S+",
    "SPACE": r"\s+",
    "DATA": r".*?",
    "GREEDYDATA": r".*",
    "IP": r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}",
    "HOSTNAME": r"[a-zA-Z0-9._-]+",
    "LOGLEVEL": r"(?:TRACE|DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|FATAL)",
    "TIMESTAMP_ISO": r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?",
    "URI_PATH": r"/[^\s?]*",
    "HTTPMETHOD": r"(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)",
    "STATUS_CODE": r"[1-5][0-9]{2}",
}


def _expand_pattern(grok_pattern: str, custom: Optional[Dict[str, str]] = None) -> str:
    """Expand %{NAME} and %{NAME:field} tokens into a regex string."""
    patterns = dict(BUILTIN_PATTERNS)
    if custom:
        patterns.update(custom)

    def replace(m: re.Match) -> str:
        token = m.group(1)
        parts = token.split(":", 1)
        name = parts[0]
        field = parts[1] if len(parts) == 2 else None
        regex = patterns.get(name)
        if regex is None:
            raise ValueError(f"Unknown grok pattern name: {name!r}")
        if field:
            return f"(?P<{field}>{regex})"
        return f"(?:{regex})"

    return re.sub(r"%\{([^}]+)\}", replace, grok_pattern)


def compile_grok(grok_pattern: str, custom: Optional[Dict[str, str]] = None) -> re.Pattern:
    """Compile a grok pattern string into a compiled regex."""
    expanded = _expand_pattern(grok_pattern, custom)
    return re.compile(expanded)


def parse_line(line: str, compiled: re.Pattern) -> Optional[Dict[str, str]]:
    """Match a line against a compiled grok pattern; return named fields or None."""
    m = compiled.search(line)
    if m is None:
        return None
    return {k: v for k, v in m.groupdict().items() if v is not None}


def parse_lines(lines: List[str], compiled: re.Pattern) -> List[Optional[Dict[str, str]]]:
    """Apply parse_line to each line; returns list of dicts (or None for non-matching)."""
    return [parse_line(line, compiled) for line in lines]


def available_builtins() -> List[str]:
    """Return sorted list of built-in grok pattern names."""
    return sorted(BUILTIN_PATTERNS.keys())
