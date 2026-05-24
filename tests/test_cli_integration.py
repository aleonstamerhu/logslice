"""Integration tests for the CLI — exercises build_parser + run together
with real (temporary) log files on disk."""

import io
import os
import sys
import tempfile
import textwrap
from unittest.mock import patch

import pytest

from logslice.cli import build_parser, run


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_LOG = textwrap.dedent("""\
    2024-01-15 08:00:01 INFO  service started
    2024-01-15 08:00:02 DEBUG config loaded
    2024-01-15 08:00:03 ERROR failed to connect to database
    2024-01-15 08:00:04 INFO  retrying connection
    2024-01-15 08:00:05 ERROR connection timeout
    2024-01-15 08:00:06 INFO  connection established
    2024-01-15 08:00:07 DEBUG cache warmed up
    2024-01-15 08:00:08 INFO  ready to serve requests
""")


def _make_log_file(content: str) -> str:
    """Write *content* to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".log", prefix="logslice_test_")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


def _run_cli(*args: str) -> tuple[int, str, str]:
    """Run the CLI with *args*, capturing stdout/stderr.

    Returns (exit_code, stdout_text, stderr_text).
    """
    parser = build_parser()
    parsed = parser.parse_args(list(args))

    out_buf = io.StringIO()
    err_buf = io.StringIO()
    exit_code = 0
    with patch("sys.stdout", out_buf), patch("sys.stderr", err_buf):
        try:
            run(parsed)
        except SystemExit as exc:
            exit_code = int(exc.code) if exc.code is not None else 0

    return exit_code, out_buf.getvalue(), err_buf.getvalue()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def log_path():
    path = _make_log_file(SAMPLE_LOG)
    yield path
    os.unlink(path)


# ---------------------------------------------------------------------------
# Basic pass-through
# ---------------------------------------------------------------------------


class TestCLIPassThrough:
    def test_all_lines_returned_without_filters(self, log_path):
        code, out, _ = _run_cli(log_path)
        assert code == 0
        lines = [l for l in out.splitlines() if l.strip()]
        assert len(lines) == 8

    def test_empty_file_produces_no_output(self):
        path = _make_log_file("")
        try:
            code, out, _ = _run_cli(path)
            assert code == 0
            assert out.strip() == ""
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Pattern filtering
# ---------------------------------------------------------------------------


class TestCLIPatternFiltering:
    def test_filter_errors(self, log_path):
        code, out, _ = _run_cli("--pattern", "ERROR", log_path)
        assert code == 0
        lines = [l for l in out.splitlines() if l.strip()]
        assert len(lines) == 2
        assert all("ERROR" in l for l in lines)

    def test_filter_case_insensitive(self, log_path):
        code, out, _ = _run_cli("--pattern", "error", "--ignore-case", log_path)
        assert code == 0
        lines = [l for l in out.splitlines() if l.strip()]
        assert len(lines) == 2

    def test_invert_match(self, log_path):
        code, out, _ = _run_cli("--pattern", "ERROR", "--invert", log_path)
        assert code == 0
        lines = [l for l in out.splitlines() if l.strip()]
        assert len(lines) == 6
        assert all("ERROR" not in l for l in lines)

    def test_no_matches_returns_empty_output(self, log_path):
        code, out, _ = _run_cli("--pattern", "CRITICAL", log_path)
        assert code == 0
        assert out.strip() == ""


# ---------------------------------------------------------------------------
# Time-range filtering
# ---------------------------------------------------------------------------


class TestCLITimeRange:
    def test_start_time_filters_early_lines(self, log_path):
        code, out, _ = _run_cli("--start", "2024-01-15T08:00:05", log_path)
        assert code == 0
        lines = [l for l in out.splitlines() if l.strip()]
        # Lines at 08:00:05, 08:00:06, 08:00:07, 08:00:08
        assert len(lines) == 4

    def test_end_time_filters_late_lines(self, log_path):
        code, out, _ = _run_cli("--end", "2024-01-15T08:00:03", log_path)
        assert code == 0
        lines = [l for l in out.splitlines() if l.strip()]
        # Lines at 08:00:01, 08:00:02, 08:00:03
        assert len(lines) == 3

    def test_combined_time_range(self, log_path):
        code, out, _ = _run_cli(
            "--start", "2024-01-15T08:00:03",
            "--end",   "2024-01-15T08:00:05",
            log_path,
        )
        assert code == 0
        lines = [l for l in out.splitlines() if l.strip()]
        assert len(lines) == 3


# ---------------------------------------------------------------------------
# Multiple sources
# ---------------------------------------------------------------------------


class TestCLIMultipleSources:
    def test_two_files_concatenated(self):
        p1 = _make_log_file("2024-01-15 08:00:01 INFO  first file\n")
        p2 = _make_log_file("2024-01-15 08:00:02 INFO  second file\n")
        try:
            code, out, _ = _run_cli(p1, p2)
            assert code == 0
            assert "first file" in out
            assert "second file" in out
        finally:
            os.unlink(p1)
            os.unlink(p2)
