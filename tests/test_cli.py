"""Tests for the CLI argument parser and runner."""

import io
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open

from logslice.cli import build_parser, run, main


class TestBuildParser:
    """Tests for build_parser argument configuration."""

    def setup_method(self):
        self.parser = build_parser()

    def test_parser_exists(self):
        assert self.parser is not None

    def test_default_no_args_requires_sources(self):
        with pytest.raises(SystemExit):
            self.parser.parse_args([])

    def test_single_source(self):
        args = self.parser.parse_args(["app.log"])
        assert args.sources == ["app.log"]

    def test_multiple_sources(self):
        args = self.parser.parse_args(["a.log", "b.log"])
        assert args.sources == ["a.log", "b.log"]

    def test_pattern_short(self):
        args = self.parser.parse_args(["-p", "ERROR", "app.log"])
        assert args.pattern == "ERROR"

    def test_pattern_long(self):
        args = self.parser.parse_args(["--pattern", "ERROR", "app.log"])
        assert args.pattern == "ERROR"

    def test_pattern_default_none(self):
        args = self.parser.parse_args(["app.log"])
        assert args.pattern is None

    def test_start_option(self):
        args = self.parser.parse_args(["--start", "2024-01-01T00:00:00", "app.log"])
        assert args.start == "2024-01-01T00:00:00"

    def test_end_option(self):
        args = self.parser.parse_args(["--end", "2024-01-02T00:00:00", "app.log"])
        assert args.end == "2024-01-02T00:00:00"

    def test_context_before_short(self):
        args = self.parser.parse_args(["-B", "3", "app.log"])
        assert args.before_context == 3

    def test_context_after_short(self):
        args = self.parser.parse_args(["-A", "2", "app.log"])
        assert args.after_context == 2

    def test_context_combined_short(self):
        args = self.parser.parse_args(["-C", "5", "app.log"])
        assert args.context == 5

    def test_count_flag(self):
        args = self.parser.parse_args(["-c", "app.log"])
        assert args.count is True

    def test_count_default_false(self):
        args = self.parser.parse_args(["app.log"])
        assert args.count is False

    def test_stats_flag(self):
        args = self.parser.parse_args(["--stats", "app.log"])
        assert args.stats is True

    def test_format_option(self):
        args = self.parser.parse_args(["--format", "numbered", "app.log"])
        assert args.format == "numbered"

    def test_format_default(self):
        args = self.parser.parse_args(["app.log"])
        assert args.format == "default"

    def test_aggregate_option(self):
        args = self.parser.parse_args(["--aggregate", r"(ERROR|WARN)", "app.log"])
        assert args.aggregate == r"(ERROR|WARN)"

    def test_invert_flag(self):
        args = self.parser.parse_args(["-v", "app.log"])
        assert args.invert is True

    def test_invert_default_false(self):
        args = self.parser.parse_args(["app.log"])
        assert args.invert is False


class TestRun:
    """Tests for the run() function with mocked pipeline."""

    def _make_args(self, **kwargs):
        """Build a minimal args namespace."""
        defaults = {
            "sources": ["app.log"],
            "pattern": None,
            "start": None,
            "end": None,
            "before_context": 0,
            "after_context": 0,
            "context": 0,
            "count": False,
            "stats": False,
            "format": "default",
            "aggregate": None,
            "invert": False,
        }
        defaults.update(kwargs)
        return MagicMock(**defaults)

    @patch("logslice.cli.run_pipeline")
    @patch("logslice.cli.open_sources")
    def test_run_calls_pipeline(self, mock_open_sources, mock_run_pipeline):
        mock_open_sources.return_value = iter(["line1\n", "line2\n"])
        mock_run_pipeline.return_value = ([], MagicMock())
        args = self._make_args()
        out = io.StringIO()
        run(args, out)
        assert mock_run_pipeline.called

    @patch("logslice.cli.run_pipeline")
    @patch("logslice.cli.open_sources")
    def test_run_count_mode(self, mock_open_sources, mock_run_pipeline):
        mock_open_sources.return_value = iter(["error here\n"])
        mock_run_pipeline.return_value = (["error here\n"], MagicMock(total=1, matched=1))
        args = self._make_args(count=True, pattern="error")
        out = io.StringIO()
        run(args, out)
        output = out.getvalue()
        assert "1" in output


class TestMain:
    """Smoke tests for the main() entry point."""

    @patch("logslice.cli.run")
    @patch("sys.argv", ["logslice", "--help"])
    def test_main_help_exits(self, mock_run):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
