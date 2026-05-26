"""Template-based output formatting for log lines.

Allows users to specify a Go-style or Python-style template string that
references named fields extracted from each log line, e.g.:

    "{timestamp} [{level}] {message}"

Fields are populated from label/field extraction; missing fields are
replaced with a configurable placeholder.
"""

import re
import string
from typing import Dict, Iterable, Iterator, Optional

_FIELD_RE = re.compile(r"\{(\w+)\}")

_DEFAULT_MISSING = "-"


def render_template(
    template: str,
    fields: Dict[str, str],
    missing: str = _DEFAULT_MISSING,
) -> str:
    """Render *template* by substituting named placeholders from *fields*.

    Any placeholder whose name is not present in *fields* is replaced with
    *missing* rather than raising a ``KeyError``.

    Args:
        template: Format string with ``{field_name}`` placeholders.
        fields:   Mapping of field names to their string values.
        missing:  Value to use when a placeholder has no corresponding field.

    Returns:
        The rendered string.

    Example::

        >>> render_template("{ts} {level}: {msg}", {"ts": "12:00", "level": "ERROR", "msg": "boom"})
        '12:00 ERROR: boom'
        >>> render_template("{ts} {level}: {msg}", {"ts": "12:00"}, missing="?")
        '12:00 ?: ?'
    """
    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        return fields.get(match.group(1), missing)

    return _FIELD_RE.sub(_replace, template)


def template_fields(template: str) -> list:
    """Return the list of unique field names referenced in *template*, in order.

    Args:
        template: Format string with ``{field_name}`` placeholders.

    Returns:
        Ordered list of unique field names.
    """
    seen: set = set()
    result = []
    for name in _FIELD_RE.findall(template):
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result


def validate_template(template: str) -> Optional[str]:
    """Check that *template* is a valid template string.

    Returns ``None`` when the template is valid, or an error message string
    when it is not (e.g. it contains bare ``{`` / ``}`` outside of valid
    placeholders).

    Args:
        template: Format string to validate.

    Returns:
        ``None`` if valid, otherwise a human-readable error description.
    """
    # Temporarily replace valid placeholders so we can detect stray braces.
    sanitised = _FIELD_RE.sub("X", template)
    if "{" in sanitised or "}" in sanitised:
        return (
            "Template contains unmatched or invalid braces. "
            "Use '{{' / '}}' to include literal braces."
        )
    return None


def apply_template(
    lines: Iterable[str],
    template: str,
    fields_fn,
    missing: str = _DEFAULT_MISSING,
) -> Iterator[str]:
    """Apply *template* to each line in *lines*, yielding rendered strings.

    Args:
        lines:     Iterable of raw log lines.
        template:  Format string with ``{field_name}`` placeholders.
        fields_fn: Callable ``(line: str) -> Dict[str, str]`` that extracts
                   fields from a single log line.
        missing:   Placeholder for absent fields.

    Yields:
        Rendered template string for each line, with a trailing newline
        preserved if the original line had one.
    """
    for line in lines:
        trailing_newline = line.endswith("\n")
        fields = fields_fn(line.rstrip("\n"))
        rendered = render_template(template, fields, missing=missing)
        yield rendered + ("\n" if trailing_newline else "")
