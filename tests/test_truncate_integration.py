"""Integration tests: truncation wired into the pipeline output."""

from logslice.truncate import truncate_lines, count_truncated
from logslice.filter import filter_lines, compile_pattern


def _run(raw_lines, pattern=None, max_length=None):
    """Filter lines then apply truncation, returning (result_lines, truncated_count)."""
    pat = compile_pattern(pattern)
    filtered = list(filter_lines(raw_lines, pattern=pat))
    truncated = truncate_lines(filtered, max_length=max_length)
    n_truncated = count_truncated(filtered, max_length=max_length)
    return truncated, n_truncated


class TestTruncateAfterFilter:
    def test_no_truncation_when_max_length_none(self):
        lines = ["ERROR: something went wrong\n", "INFO: all good\n"]
        result, n = _run(lines, pattern="ERROR", max_length=None)
        assert result == ["ERROR: something went wrong\n"]
        assert n == 0

    def test_truncates_long_filtered_lines(self):
        long_msg = "ERROR: " + "x" * 100
        lines = [long_msg + "\n", "INFO: ok\n"]
        result, n = _run(lines, pattern="ERROR", max_length=20)
        assert len(result) == 1
        assert result[0].rstrip("\n").endswith("...")
        assert len(result[0].rstrip("\n")) == 23  # 20 chars + "..."
        assert n == 1

    def test_short_lines_pass_through_unchanged(self):
        lines = ["WARN: disk low\n", "ERROR: timeout\n"]
        result, n = _run(lines, pattern=None, max_length=50)
        assert result == lines
        assert n == 0

    def test_empty_input(self):
        result, n = _run([], pattern="ERROR", max_length=10)
        assert result == []
        assert n == 0

    def test_no_pattern_all_lines_truncated_if_long(self):
        lines = ["a" * 30 + "\n", "b" * 30 + "\n", "short\n"]
        result, n = _run(lines, pattern=None, max_length=10)
        assert n == 2
        assert result[2] == "short\n"
        for r in result[:2]:
            assert r.rstrip("\n").endswith("...")

    def test_count_matches_truncated_count(self):
        lines = [
            "DEBUG: " + "v" * 80 + "\n",
            "DEBUG: short\n",
            "INFO: not matched\n",
        ]
        result, n = _run(lines, pattern="DEBUG", max_length=15)
        assert len(result) == 2
        assert n == 1  # only the long DEBUG line exceeds 15 chars
