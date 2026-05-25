"""Redaction utilities for masking sensitive data in log lines."""

import re
from typing import Iterable, Iterator, List, Optional, Tuple

# Built-in redaction patterns: (name, pattern, replacement)
_BUILTIN_PATTERNS: List[Tuple[str, re.Pattern, str]] = [
    (
        "password",
        re.compile(r'(?i)(password|passwd|pwd)([=:\s]+)\S+'),
        r'\1\2[REDACTED]',
    ),
    (
        "token",
        re.compile(r'(?i)(token|api[_-]?key|secret)([=:\s]+)\S+'),
        r'\1\2[REDACTED]',
    ),
    (
        "email",
        re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+'),
        '[EMAIL]',
    ),
    (
        "ipv4",
        re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
        '[IPv4]',
    ),
    (
        "credit_card",
        re.compile(r'\b(?:\d[ -]?){13,16}\b'),
        '[CC]',
    ),
]


def compile_redaction(pattern: str, replacement: str = '[REDACTED]') -> Tuple[re.Pattern, str]:
    """Compile a custom redaction pattern."""
    return re.compile(pattern), replacement


def redact_line(
    line: str,
    builtins: Optional[List[str]] = None,
    custom: Optional[List[Tuple[re.Pattern, str]]] = None,
) -> str:
    """Apply redaction rules to a single line.

    Args:
        line: The log line to redact.
        builtins: List of built-in rule names to apply. None means all.
        custom: List of (compiled_pattern, replacement) tuples.

    Returns:
        The redacted line.
    """
    result = line

    for name, pattern, repl in _BUILTIN_PATTERNS:
        if builtins is None or name in builtins:
            result = pattern.sub(repl, result)

    if custom:
        for pattern, repl in custom:
            result = pattern.sub(repl, result)

    return result


def redact_lines(
    lines: Iterable[str],
    builtins: Optional[List[str]] = None,
    custom: Optional[List[Tuple[re.Pattern, str]]] = None,
) -> Iterator[str]:
    """Apply redaction to an iterable of log lines."""
    for line in lines:
        yield redact_line(line, builtins=builtins, custom=custom)


def available_builtins() -> List[str]:
    """Return the names of all built-in redaction rules."""
    return [name for name, _, _ in _BUILTIN_PATTERNS]
