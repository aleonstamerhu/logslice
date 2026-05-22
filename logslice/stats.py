"""Statistics collection and reporting for log filtering results."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FilterStats:
    """Holds statistics gathered during a log filtering run."""

    total_lines: int = 0
    matched_lines: int = 0
    skipped_lines: int = 0
    time_filtered_lines: int = 0
    pattern_filtered_lines: int = 0
    parse_errors: int = 0
    sources_processed: int = 0

    @property
    def match_rate(self) -> float:
        """Return fraction of total lines that matched (0.0 if no lines)."""
        if self.total_lines == 0:
            return 0.0
        return self.matched_lines / self.total_lines

    @property
    def match_percent(self) -> float:
        """Return percentage of total lines that matched."""
        return self.match_rate * 100.0


def collect_stats(
    lines: list[str],
    matched: list[str],
    time_filtered: int = 0,
    pattern_filtered: int = 0,
    parse_errors: int = 0,
    sources: int = 1,
) -> FilterStats:
    """Build a FilterStats object from raw counts."""
    total = len(lines)
    matched_count = len(matched)
    skipped = total - matched_count - time_filtered - pattern_filtered
    return FilterStats(
        total_lines=total,
        matched_lines=matched_count,
        skipped_lines=max(skipped, 0),
        time_filtered_lines=time_filtered,
        pattern_filtered_lines=pattern_filtered,
        parse_errors=parse_errors,
        sources_processed=sources,
    )


def format_stats(stats: FilterStats, verbose: bool = False) -> str:
    """Return a human-readable summary string for the given stats."""
    lines = [
        f"Sources processed : {stats.sources_processed}",
        f"Total lines       : {stats.total_lines}",
        f"Matched lines     : {stats.matched_lines} ({stats.match_percent:.1f}%)",
    ]
    if verbose:
        lines += [
            f"Time-filtered     : {stats.time_filtered_lines}",
            f"Pattern-filtered  : {stats.pattern_filtered_lines}",
            f"Parse errors      : {stats.parse_errors}",
        ]
    return "\n".join(lines)
