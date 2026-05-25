"""Integration tests: label filtering combined with pattern filtering."""

from logslice.labelfilter import filter_by_labels
from logslice.filter import compile_pattern, filter_lines

LOG_LINES = [
    "2024-01-15T10:00:01 level=error host=web01 env=prod msg=\"disk full\"",
    "2024-01-15T10:00:02 level=warn  host=web01 env=prod msg=\"high load\"",
    "2024-01-15T10:00:03 level=error host=db01  env=staging msg=\"conn timeout\"",
    "2024-01-15T10:00:04 level=info  host=web01 env=prod msg=\"request ok\"",
    "2024-01-15T10:00:05 level=error host=web02 env=prod msg=\"oom killed\"",
]


def _run(lines, label_exprs, pattern=None):
    result = list(filter_by_labels(lines, label_exprs))
    if pattern is not None:
        pat = compile_pattern(pattern)
        result = list(filter_lines(result, pattern=pat))
    return result


def test_label_only_errors():
    result = _run(LOG_LINES, ["level=error"])
    assert len(result) == 3


def test_label_prod_errors():
    result = _run(LOG_LINES, ["level=error", "env=prod"])
    assert len(result) == 2
    assert all("env=prod" in l for l in result)


def test_label_then_pattern():
    result = _run(LOG_LINES, ["level=error"], pattern=r"disk|oom")
    assert len(result) == 2
    assert any("disk full" in l for l in result)
    assert any("oom killed" in l for l in result)


def test_negated_staging_errors():
    result = _run(LOG_LINES, ["level=error", "!env=staging"])
    assert len(result) == 2
    assert all("env=staging" not in l for l in result)


def test_no_matches_returns_empty():
    result = _run(LOG_LINES, ["level=critical"])
    assert result == []


def test_label_filter_preserves_line_content():
    result = _run(LOG_LINES, ["host=db01"])
    assert len(result) == 1
    assert "conn timeout" in result[0]


def test_empty_log_returns_empty():
    assert _run([], ["level=error"]) == []
