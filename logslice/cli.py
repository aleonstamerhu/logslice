"""Command-line interface for logslice."""

import argparse
import sys
from typing import List, Optional

from logslice.filter import compile_pattern, filter_lines
from logslice.time_range import parse_range


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log filtering and aggregation with regex and time-range support.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Log files to process (default: stdin).",
    )
    parser.add_argument(
        "-p", "--pattern",
        metavar="REGEX",
        help="Regex pattern to filter lines.",
    )
    parser.add_argument(
        "-v", "--invert",
        action="store_true",
        help="Invert pattern match (exclude matching lines).",
    )
    parser.add_argument(
        "-s", "--start",
        metavar="TIMESTAMP",
        help="Start of time range (inclusive).",
    )
    parser.add_argument(
        "-e", "--end",
        metavar="TIMESTAMP",
        help="End of time range (inclusive).",
    )
    parser.add_argument(
        "-c", "--count",
        action="store_true",
        help="Print count of matching lines instead of the lines themselves.",
    )
    return parser


def run(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    pattern = compile_pattern(args.pattern) if args.pattern else None
    time_range = parse_range(args.start, args.end) if (args.start or args.end) else None

    def open_sources():
        if args.files:
            for path in args.files:
                with open(path, "r", errors="replace") as fh:
                    yield from fh
        else:
            yield from sys.stdin

    matched = filter_lines(
        open_sources(),
        pattern=pattern,
        time_range=time_range,
        invert=args.invert,
    )

    if args.count:
        print(sum(1 for _ in matched))
    else:
        for line in matched:
            print(line)

    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
