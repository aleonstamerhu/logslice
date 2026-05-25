"""Integration tests: rate limiting after pattern filtering."""

from logslice.filter import filter_lines, compile_pattern
from logslice.rate import rate_limit, count_suppressed


def _run(raw_lines, pattern=None, max_per_bucket=None, bucket_seconds=60):
    pattern_re = compile_pattern(pattern)
    filtered = list(filter_lines(raw_lines, pattern_re))
    if max_per_bucket is not None:
        return list(rate_limit(filtered, max_per_bucket, bucket_seconds))
    return filtered


LOG = [
    "2024-01-15T10:00:01 ERROR disk full",
    "2024-01-15T10:00:02 ERROR disk full",
    "2024-01-15T10:00:03 ERROR disk full",
    "2024-01-15T10:00:04 WARN low memory",
    "2024-01-15T10:01:01 ERROR disk full",
    "2024-01-15T10:01:02 ERROR disk full",
]


def test_no_rate_limit_returns_all_errors():
    result = _run(LOG, pattern="ERROR")
    assert len(result) == 5


def test_rate_limit_one_error_per_minute():
    result = _run(LOG, pattern="ERROR", max_per_bucket=1, bucket_seconds=60)
    assert result == [
        "2024-01-15T10:00:01 ERROR disk full",
        "2024-01-15T10:01:01 ERROR disk full",
    ]


def test_rate_limit_two_errors_per_minute():
    result = _run(LOG, pattern="ERROR", max_per_bucket=2, bucket_seconds=60)
    assert len(result) == 4


def test_no_pattern_rate_limits_all():
    result = _run(LOG, pattern=None, max_per_bucket=1, bucket_seconds=60)
    assert result == [LOG[0]]


def test_count_suppressed_after_filter():
    pattern_re = compile_pattern("ERROR")
    filtered = list(filter_lines(LOG, pattern_re))
    suppressed = count_suppressed(filtered, 1, bucket_seconds=60)
    assert suppressed == 3
