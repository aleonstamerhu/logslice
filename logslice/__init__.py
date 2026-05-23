"""logslice — Fast log filtering and aggregation utility with regex and time-range support."""

__version__ = "0.1.0"
__author__ = "logslice contributors"
__license__ = "MIT"

from logslice.filter import compile_pattern, filter_lines, count_matches
from logslice.extractor import extract_timestamp
from logslice.time_range import parse_timestamp, parse_range, within_range
from logslice.pipeline import run_pipeline

__all__ = [
    "compile_pattern",
    "filter_lines",
    "count_matches",
    "extract_timestamp",
    "parse_timestamp",
    "parse_range",
    "within_range",
    "run_pipeline",
]
