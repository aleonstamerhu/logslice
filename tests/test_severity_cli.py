"""CLI-level tests for --min-level / --max-level severity filtering."""

import io
import sys
from unittest.mock import patch

import pytest

from logslice.cli import build_parser, run


LOG = [
    "[debug] verbose detail",
    "[info] started ok",
    "[warn] high load",
    "[error] disk full",
    "[fatal] kernel panic",
]


def _run_with_lines(args, lines):
    """Run the CLI pipeline over an in-memory list of lines."""
    parser = build_parser()
    ns = parser.parse_args(args)
    buf = io.StringIO()
    with patch("logslice.cli.open_sources", return_value=iter(lines)):
        with patch("sys.stdout", buf):
            run(ns)
    return buf.getvalue().splitlines()


def test_parser_accepts_min_level():
    parser = build_parser()
    ns = parser.parse_args(["--min-level", "error", "app.log"])
    assert ns.min_level == "error"


def test_parser_accepts_max_level():
    parser = build_parser()
    ns = parser.parse_args(["--min-level", "warn", "--max-level", "error", "app.log"])
    assert ns.max_level == "error"


def test_parser_min_level_default_none():
    parser = build_parser()
    ns = parser.parse_args(["app.log"])
    assert getattr(ns, "min_level", None) is None


def test_min_level_error_filters_correctly():
    result = _run_with_lines(["--min-level", "error", "-"], LOG)
    assert any("[error]" in l for l in result)
    assert any("[fatal]" in l for l in result)
    assert not any("[warn]" in l for l in result)
    assert not any("[info]" in l for l in result)


def test_min_level_warn_max_level_error():
    result = _run_with_lines(["--min-level", "warn", "--max-level", "error", "-"], LOG)
    assert any("[warn]" in l for l in result)
    assert any("[error]" in l for l in result)
    assert not any("[fatal]" in l for l in result)
    assert not any("[debug]" in l for l in result)


def test_no_severity_flags_returns_all():
    result = _run_with_lines(["-"], LOG)
    assert len(result) == len(LOG)
