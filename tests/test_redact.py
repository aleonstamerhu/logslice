"""Tests for logslice.redact."""

import re
import pytest
from logslice.redact import (
    available_builtins,
    compile_redaction,
    redact_line,
    redact_lines,
)


class TestAvailableBuiltins:
    def test_returns_list(self):
        assert isinstance(available_builtins(), list)

    def test_known_names_present(self):
        names = available_builtins()
        for name in ("password", "token", "email", "ipv4", "credit_card"):
            assert name in names


class TestCompileRedaction:
    def test_returns_tuple(self):
        result = compile_redaction(r'\d+')
        assert isinstance(result, tuple) and len(result) == 2

    def test_default_replacement(self):
        _, repl = compile_redaction(r'\d+')
        assert repl == '[REDACTED]'

    def test_custom_replacement(self):
        _, repl = compile_redaction(r'\d+', '[NUM]')
        assert repl == '[NUM]'


class TestRedactLine:
    def test_no_sensitive_data_unchanged(self):
        line = '2024-01-01 INFO starting server'
        assert redact_line(line) == line

    def test_password_redacted(self):
        line = 'login password=secret123 failed'
        result = redact_line(line, builtins=['password'])
        assert 'secret123' not in result
        assert '[REDACTED]' in result

    def test_token_redacted(self):
        line = 'auth token=abc.def.ghi ok'
        result = redact_line(line, builtins=['token'])
        assert 'abc.def.ghi' not in result
        assert '[REDACTED]' in result

    def test_email_redacted(self):
        line = 'user user@example.com logged in'
        result = redact_line(line, builtins=['email'])
        assert 'user@example.com' not in result
        assert '[EMAIL]' in result

    def test_ipv4_redacted(self):
        line = 'connection from 192.168.1.42 accepted'
        result = redact_line(line, builtins=['ipv4'])
        assert '192.168.1.42' not in result
        assert '[IPv4]' in result

    def test_credit_card_redacted(self):
        line = 'card 4111111111111111 charged'
        result = redact_line(line, builtins=['credit_card'])
        assert '4111111111111111' not in result
        assert '[CC]' in result

    def test_none_builtins_applies_all(self):
        line = 'user@example.com password=hunter2'
        result = redact_line(line, builtins=None)
        assert 'user@example.com' not in result
        assert 'hunter2' not in result

    def test_empty_builtins_skips_all_builtins(self):
        line = 'user@example.com password=hunter2'
        result = redact_line(line, builtins=[])
        assert result == line

    def test_custom_pattern_applied(self):
        pattern, repl = compile_redaction(r'\bORDER-\d+\b', '[ORDER]')
        line = 'processing ORDER-98765 for user'
        result = redact_line(line, builtins=[], custom=[(pattern, repl)])
        assert 'ORDER-98765' not in result
        assert '[ORDER]' in result

    def test_custom_and_builtin_combined(self):
        pattern, repl = compile_redaction(r'\bORDER-\d+\b', '[ORDER]')
        line = 'ORDER-123 from user@example.com'
        result = redact_line(line, builtins=['email'], custom=[(pattern, repl)])
        assert '[EMAIL]' in result
        assert '[ORDER]' in result


class TestRedactLines:
    def test_empty_input(self):
        assert list(redact_lines([])) == []

    def test_multiple_lines(self):
        lines = [
            'INFO server started',
            'DEBUG password=s3cr3t set',
            'WARN user@host.com failed',
        ]
        results = list(redact_lines(lines, builtins=['password', 'email']))
        assert results[0] == 'INFO server started'
        assert 's3cr3t' not in results[1]
        assert 'user@host.com' not in results[2]

    def test_returns_iterator(self):
        import types
        result = redact_lines(['hello'], builtins=[])
        assert isinstance(result, types.GeneratorType)
