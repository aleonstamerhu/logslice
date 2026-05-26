"""logslice — Fast log filtering and aggregation utility."""

from logslice.filter import compile_pattern, filter_lines, count_matches
from logslice.time_range import parse_timestamp, parse_range, within_range
from logslice.extractor import extract_timestamp
from logslice.aggregator import aggregate_by_pattern, aggregate_by_time_bucket, format_aggregation
from logslice.formatter import get_format_template, format_line, format_lines
from logslice.context import lines_with_context, extract_lines
from logslice.stats import FilterStats, collect_stats, format_stats
from logslice.pipeline import run_pipeline
from logslice.dedup import deduplicate, count_duplicates
from logslice.highlight import highlight_match, highlight_lines
from logslice.truncate import truncate_line, truncate_lines
from logslice.tail import tail_lines, head_lines
from logslice.sample import sample_by_rate, reservoir_sample, every_nth
from logslice.burst import detect_bursts, format_burst
from logslice.fold import fold_lines, count_folded
from logslice.rate import rate_limit, count_suppressed
from logslice.fieldextract import extract_fields, filter_by_field
from logslice.severity import parse_level, extract_level, filter_by_severity

__all__ = [
    "compile_pattern", "filter_lines", "count_matches",
    "parse_timestamp", "parse_range", "within_range",
    "extract_timestamp",
    "aggregate_by_pattern", "aggregate_by_time_bucket", "format_aggregation",
    "get_format_template", "format_line", "format_lines",
    "lines_with_context", "extract_lines",
    "FilterStats", "collect_stats", "format_stats",
    "run_pipeline",
    "deduplicate", "count_duplicates",
    "highlight_match", "highlight_lines",
    "truncate_line", "truncate_lines",
    "tail_lines", "head_lines",
    "sample_by_rate", "reservoir_sample", "every_nth",
    "detect_bursts", "format_burst",
    "fold_lines", "count_folded",
    "rate_limit", "count_suppressed",
    "extract_fields", "filter_by_field",
    "parse_level", "extract_level", "filter_by_severity",
]
