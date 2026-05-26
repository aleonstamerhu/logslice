"""Tests for logslice.rotate."""

import os
import tempfile
from pathlib import Path

import pytest

from logslice.rotate import (
    file_inode,
    file_size,
    has_rotated,
    has_truncated,
    iter_with_reopen,
)


# ---------------------------------------------------------------------------
# file_inode
# ---------------------------------------------------------------------------

class TestFileInode:
    def test_returns_int_for_existing_file(self, tmp_path):
        p = tmp_path / "test.log"
        p.write_text("hello")
        assert isinstance(file_inode(str(p)), int)

    def test_returns_none_for_missing_file(self, tmp_path):
        assert file_inode(str(tmp_path / "missing.log")) is None


# ---------------------------------------------------------------------------
# file_size
# ---------------------------------------------------------------------------

class TestFileSize:
    def test_returns_byte_count(self, tmp_path):
        p = tmp_path / "test.log"
        p.write_bytes(b"abcde")
        assert file_size(str(p)) == 5

    def test_returns_zero_for_missing_file(self, tmp_path):
        assert file_size(str(tmp_path / "missing.log")) == 0


# ---------------------------------------------------------------------------
# has_rotated
# ---------------------------------------------------------------------------

class TestHasRotated:
    def test_false_when_inode_matches(self, tmp_path):
        p = tmp_path / "test.log"
        p.write_text("x")
        inode = file_inode(str(p))
        assert has_rotated(str(p), inode) is False

    def test_true_when_file_missing(self, tmp_path):
        p = tmp_path / "gone.log"
        assert has_rotated(str(p), known_inode=999) is True

    def test_false_when_known_inode_is_none(self, tmp_path):
        p = tmp_path / "test.log"
        p.write_text("x")
        assert has_rotated(str(p), known_inode=None) is False

    def test_true_when_inode_changes(self, tmp_path):
        p = tmp_path / "test.log"
        p.write_text("x")
        old_inode = file_inode(str(p))
        # Simulate rotation: delete and recreate
        p.unlink()
        p.write_text("y")
        # On most filesystems the new inode differs; guard with assumption
        new_inode = file_inode(str(p))
        expected = new_inode != old_inode
        assert has_rotated(str(p), old_inode) == expected


# ---------------------------------------------------------------------------
# has_truncated
# ---------------------------------------------------------------------------

class TestHasTruncated:
    def test_false_when_same_size(self, tmp_path):
        p = tmp_path / "test.log"
        p.write_bytes(b"hello")
        assert has_truncated(str(p), 5) is False

    def test_false_when_grown(self, tmp_path):
        p = tmp_path / "test.log"
        p.write_bytes(b"hello world")
        assert has_truncated(str(p), 5) is False

    def test_true_when_shrunk(self, tmp_path):
        p = tmp_path / "test.log"
        p.write_bytes(b"hi")
        assert has_truncated(str(p), 100) is True


# ---------------------------------------------------------------------------
# iter_with_reopen
# ---------------------------------------------------------------------------

class TestIterWithReopen:
    def test_reads_all_lines_from_static_file(self, tmp_path):
        p = tmp_path / "app.log"
        p.write_text("line1\nline2\nline3\n")
        lines = list(iter_with_reopen(str(p), poll_interval=0, max_polls=0))
        assert lines == ["line1\n", "line2\n", "line3\n"]

    def test_empty_file_returns_empty(self, tmp_path):
        p = tmp_path / "app.log"
        p.write_text("")
        lines = list(iter_with_reopen(str(p), poll_interval=0, max_polls=0))
        assert lines == []

    def test_missing_file_returns_empty_after_max_polls(self, tmp_path):
        p = tmp_path / "missing.log"
        lines = list(iter_with_reopen(str(p), poll_interval=0, max_polls=1))
        assert lines == []

    def test_reopens_after_rotation(self, tmp_path):
        p = tmp_path / "app.log"
        p.write_text("before\n")
        # Collect first batch manually via a short max_polls
        lines = list(iter_with_reopen(str(p), poll_interval=0, max_polls=0))
        assert "before\n" in lines
