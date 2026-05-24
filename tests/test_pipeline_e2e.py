"""End-to-end tests for the full logslice pipeline with real-world log samples."""

import io
from datetime import datetime, timezone

import pytest

from logslice.pipeline import run_pipeline


APACHE_LOGS = [
    '2024-01-15 08:00:01 INFO GET /index.html 200 1234',
    '2024-01-15 08:00:02 ERROR GET /missing.html 404 512',
    '2024-01-15 08:00:03 INFO POST /api/data 201 890',
    '2024-01-15 08:00:04 WARN GET /slow.php 200 9999',
    '2024-01-15 08:00:05 ERROR POST /api/login 500 256',
    '2024-01-15 08:00:06 INFO GET /favicon.ico 200 100',
    '2024-01-15 08:00:07 DEBUG GET /healthcheck 200 50',
    '2024-01-15 08:00:08 ERROR DELETE /api/user 403 300',
]

SYSLOG_LOGS = [
    'Jan 15 08:00:01 host kernel: usb 1-1: new device found',
    'Jan 15 08:00:02 host sshd[1234]: Failed password for root',
    'Jan 15 08:00:03 host sshd[1234]: Accepted publickey for admin',
    'Jan 15 08:00:04 host kernel: EXT4-fs error on device sda1',
    'Jan 15 08:00:05 host cron[5678]: job started: backup.sh',
    'Jan 15 08:00:06 host sshd[1234]: Failed password for guest',
]


def _run(lines, **kwargs):
    """Run the pipeline over a list of strings and return matched lines."""
    output = []
    run_pipeline(iter(lines), output.append, **kwargs)
    return output


class TestE2EPatternFiltering:
    def test_filter_errors_only(self):
        results = _run(APACHE_LOGS, pattern=r'ERROR')
        assert len(results) == 3
        assert all('ERROR' in line for line in results)

    def test_filter_by_http_method(self):
        results = _run(APACHE_LOGS, pattern=r' POST ')
        assert len(results) == 2
        assert all('POST' in line for line in results)

    def test_filter_by_status_code(self):
        results = _run(APACHE_LOGS, pattern=r' 200 ')
        assert len(results) == 4

    def test_case_insensitive_filter(self):
        results = _run(APACHE_LOGS, pattern=r'error', flags_ignore_case=True)
        assert len(results) == 3

    def test_no_pattern_returns_all(self):
        results = _run(APACHE_LOGS)
        assert results == APACHE_LOGS

    def test_pattern_no_match_returns_empty(self):
        results = _run(APACHE_LOGS, pattern=r'CRITICAL')
        assert results == []


class TestE2ESyslogFiltering:
    def test_filter_ssh_failures(self):
        results = _run(SYSLOG_LOGS, pattern=r'Failed password')
        assert len(results) == 2

    def test_filter_kernel_messages(self):
        results = _run(SYSLOG_LOGS, pattern=r'kernel:')
        assert len(results) == 2

    def test_filter_sshd_process(self):
        results = _run(SYSLOG_LOGS, pattern=r'sshd\[')
        assert len(results) == 3


class TestE2EContextLines:
    def test_error_with_before_context(self):
        results = _run(APACHE_LOGS, pattern=r'ERROR', before_context=1)
        # Each ERROR match may include one preceding line
        assert len(results) >= 3
        assert any('ERROR' in line for line in results)

    def test_error_with_after_context(self):
        results = _run(APACHE_LOGS, pattern=r'ERROR', after_context=1)
        assert len(results) >= 3

    def test_error_with_surrounding_context(self):
        results = _run(APACHE_LOGS, pattern=r'ERROR', before_context=1, after_context=1)
        assert len(results) >= 3


class TestE2EEmptyAndEdgeCases:
    def test_empty_input(self):
        results = _run([])
        assert results == []

    def test_single_matching_line(self):
        results = _run(['2024-01-15 ERROR something went wrong'], pattern=r'ERROR')
        assert results == ['2024-01-15 ERROR something went wrong']

    def test_single_non_matching_line(self):
        results = _run(['2024-01-15 INFO all good'], pattern=r'ERROR')
        assert results == []

    def test_lines_with_special_regex_chars(self):
        lines = [
            'price: $100.00',
            'discount: 10%',
            'total: $90.00',
        ]
        results = _run(lines, pattern=r'\$\d+')
        assert len(results) == 2
        assert all('$' in line for line in results)

    def test_multiline_pattern_anchors(self):
        lines = ['ERROR: start of line', 'some ERROR in middle']
        results = _run(lines, pattern=r'^ERROR')
        assert len(results) == 1
        assert results[0].startswith('ERROR')
