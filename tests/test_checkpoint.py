"""Tests for logslice.checkpoint."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from logslice.checkpoint import (
    clear_checkpoint,
    iter_from_checkpoint,
    load_offset,
    save_offset,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ckdir(tmp_path: Path) -> Path:
    d = tmp_path / "checkpoints"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# load_offset
# ---------------------------------------------------------------------------


def test_load_offset_missing_returns_zero(tmp_path):
    assert load_offset("app.log", _ckdir(tmp_path)) == 0


def test_load_offset_returns_saved_value(tmp_path):
    d = _ckdir(tmp_path)
    save_offset("app.log", 1024, d)
    assert load_offset("app.log", d) == 1024


def test_load_offset_corrupt_file_returns_zero(tmp_path):
    d = _ckdir(tmp_path)
    (d / "app.log.json").write_text("not-json")
    assert load_offset("app.log", d) == 0


# ---------------------------------------------------------------------------
# save_offset
# ---------------------------------------------------------------------------


def test_save_offset_creates_file(tmp_path):
    d = _ckdir(tmp_path)
    save_offset("syslog", 512, d)
    path = d / "syslog.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["offset"] == 512
    assert data["source"] == "syslog"


def test_save_offset_overwrites_previous(tmp_path):
    d = _ckdir(tmp_path)
    save_offset("syslog", 100, d)
    save_offset("syslog", 200, d)
    assert load_offset("syslog", d) == 200


def test_save_offset_creates_directory(tmp_path):
    d = tmp_path / "new" / "nested"
    save_offset("app.log", 42, d)
    assert load_offset("app.log", d) == 42


# ---------------------------------------------------------------------------
# clear_checkpoint
# ---------------------------------------------------------------------------


def test_clear_existing_checkpoint_returns_true(tmp_path):
    d = _ckdir(tmp_path)
    save_offset("app.log", 10, d)
    assert clear_checkpoint("app.log", d) is True
    assert load_offset("app.log", d) == 0


def test_clear_nonexistent_checkpoint_returns_false(tmp_path):
    d = _ckdir(tmp_path)
    assert clear_checkpoint("ghost.log", d) is False


# ---------------------------------------------------------------------------
# iter_from_checkpoint
# ---------------------------------------------------------------------------


def test_iter_reads_all_lines_from_start(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("line1\nline2\nline3\n")
    d = _ckdir(tmp_path)
    lines = list(iter_from_checkpoint(str(log), d))
    assert lines == ["line1\n", "line2\n", "line3\n"]


def test_iter_updates_checkpoint(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("hello\nworld\n")
    d = _ckdir(tmp_path)
    list(iter_from_checkpoint(str(log), d))
    assert load_offset(str(log), d) == len(b"hello\nworld\n")


def test_iter_resumes_from_saved_offset(tmp_path):
    log = tmp_path / "app.log"
    log.write_bytes(b"first\nsecond\n")
    d = _ckdir(tmp_path)
    # Simulate first run consumed "first\n"
    save_offset(str(log), len(b"first\n"), d)
    lines = list(iter_from_checkpoint(str(log), d))
    assert lines == ["second\n"]


def test_iter_no_update_leaves_checkpoint_unchanged(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("data\n")
    d = _ckdir(tmp_path)
    list(iter_from_checkpoint(str(log), d, update=False))
    assert load_offset(str(log), d) == 0
