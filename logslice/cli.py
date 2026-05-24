"""Command-line interface for logslice."""

import argparse
import sys
from typing import Iterator

from logslice import __version__
from logslice.pipeline import run_pipeline
from logslice.output import write_lines, write_summary
from logslice.highlight import highlight_lines, supports_color


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log filtering and aggregation utility.",
    )
    parser.add_argument("sources", nargs="*", metavar="FILE", help="Log files to read (default: stdin)")
    parser.add_argument("-p", "--pattern", help="Regex pattern to filter lines")
    parser.add_argument("-v", "--invert", action="store_true", help="Invert pattern match")
    parser.add_argument("--start", help="Start of time range (ISO or syslog timestamp)")
    parser.add_argument("--end", help="End of time range (ISO or syslog timestamp)")
    parser.add_argument("-B", "--before-context", type=int, default=0, metavar="N")
    parser.add_argument("-A", "--after-context", type=int, default=0, metavar="N")
    parser.add_argument("--dedup", action="store_true", help="Remove duplicate lines")
    parser.add_argument("--ignore-timestamps", action="store_true", help="Ignore timestamps when deduplicating")
    parser.add_argument("--stats", action="store_true", help="Print match statistics to stderr")
    parser.add_argument("--color", choices=["auto", "always", "never"], default="auto", help="Highlight matched text")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def open_sources(sources: list[str]) -> Iterator[str]:
    if not sources:
        yield from sys.stdin
        return
    for path in sources:
        with open(path, "r", errors="replace") as fh:
            yield from fh


def run(argv: list[str] | None = None, stdout=None, stderr=None) -> int:
    if stdout is None:
        stdout = sys.stdout
    if stderr is None:
        stderr = sys.stderr

    parser = build_parser()
    args = parser.parse_args(argv)

    lines = list(open_sources(args.sources))

    result = run_pipeline(
        lines,
        pattern=args.pattern,
        invert=args.invert,
        start=args.start,
        end=args.end,
        before_context=args.before_context,
        after_context=args.after_context,
        dedup=args.dedup,
        ignore_timestamps=args.ignore_timestamps,
    )

    color_enabled = (
        args.color == "always"
        or (args.color == "auto" and supports_color(stdout))
    )

    from logslice.filter import compile_pattern
    compiled = compile_pattern(args.pattern) if args.pattern else None
    output_lines = highlight_lines(result.lines, compiled, enabled=color_enabled)

    write_lines(output_lines, stdout)

    if args.stats:
        from logslice.stats import collect_stats, format_stats
        stats = collect_stats(lines, result.lines)
        write_summary(format_stats(stats), stderr)

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run())
