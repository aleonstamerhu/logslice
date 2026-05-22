"""High-level pipeline that wires together filtering, context, and stats."""

from typing import Iterable, Optional

from logslice.extractor import extract_timestamp
from logslice.filter import compile_pattern, filter_lines
from logslice.context import lines_with_context
from logslice.time_range import parse_range, within_range
from logslice.stats import FilterStats, collect_stats


def run_pipeline(
    raw_lines: list[str],
    *,
    pattern: Optional[str] = None,
    time_range: Optional[str] = None,
    before_context: int = 0,
    after_context: int = 0,
    ignore_case: bool = False,
) -> tuple[list[str], FilterStats]:
    """Filter *raw_lines* and return (result_lines, stats).

    Parameters
    ----------
    raw_lines:
        All log lines to process.
    pattern:
        Optional regex pattern to match against each line.
    time_range:
        Optional time range string understood by :func:`parse_range`.
    before_context:
        Number of lines to include before each match.
    after_context:
        Number of lines to include after each match.
    ignore_case:
        Whether regex matching should be case-insensitive.
    """
    compiled = compile_pattern(pattern, ignore_case=ignore_case) if pattern else None
    time_rng = parse_range(time_range) if time_range else None

    time_filtered = 0
    pattern_filtered = 0
    parse_errors = 0
    candidate_lines: list[str] = []

    for line in raw_lines:
        # --- time range filter ---
        if time_rng is not None:
            ts = extract_timestamp(line)
            if ts is None:
                parse_errors += 1
            elif not within_range(ts, time_rng):
                time_filtered += 1
                continue

        candidate_lines.append(line)

    # --- pattern filter ---
    if compiled is not None:
        filtered = list(filter_lines(candidate_lines, compiled))
        pattern_filtered = len(candidate_lines) - len(filtered)
    else:
        filtered = candidate_lines

    # --- context expansion ---
    def _is_match(line: str) -> bool:
        if compiled is None:
            return True
        return compiled.search(line) is not None

    if before_context > 0 or after_context > 0:
        result = list(
            lines_with_context(
                candidate_lines,
                _is_match,
                before=before_context,
                after=after_context,
            )
        )
    else:
        result = filtered

    stats = collect_stats(
        raw_lines,
        result,
        time_filtered=time_filtered,
        pattern_filtered=pattern_filtered,
        parse_errors=parse_errors,
    )
    return result, stats
