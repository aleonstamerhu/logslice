"""Integration tests: checkpoint + pipeline for incremental log processing."""

from __future__ import annotations

from pathlib import Path

from logslice.checkpoint import iter_from_checkpoint, load_offset, save_offset
from logslice.filter import compile_pattern, filter_lines


def _run(log_path: str, pattern: str | None, ck_dir: Path) -> list[str]:
    raw = iter_from_checkpoint(log_path, ck_dir)
    pat = compile_pattern(pattern)
    return list(filter_lines(raw, pattern=pat))


# ---------------------------------------------------------------------------
# Incremental reads through the pipeline
# ---------------------------------------------------------------------------


def test_first_run_processes_all_lines(tmp_path):
    log = tmp_path / "service.log"
    log.write_text("INFO start\nERROR boom\nINFO end\n")
    d = tmp_path / "ck"
    results = _run(str(log), r"ERROR", d)
    assert results == ["ERROR boom\n"]


def test_second_run_skips_already_processed(tmp_path):
    log = tmp_path / "service.log"
    initial = "INFO start\nERROR boom\n"
    log.write_text(initial)
    d = tmp_path / "ck"
    # First pass
    _run(str(log), None, d)
    offset_after_first = load_offset(str(log), d)
    assert offset_after_first == len(initial.encode())
    # Append new content
    log.write_text(initial + "ERROR second\nINFO done\n")
    results = _run(str(log), r"ERROR", d)
    assert results == ["ERROR second\n"]


def test_incremental_reads_accumulate_correctly(tmp_path):
    log = tmp_path / "app.log"
    d = tmp_path / "ck"
    chunks = [
        "WARN  first\n",
        "ERROR alpha\n",
        "ERROR beta\n",
        "INFO  last\n",
    ]
    collected: list[str] = []
    written = ""
    for chunk in chunks:
        written += chunk
        log.write_text(written)
        collected.extend(_run(str(log), r"ERROR", d))
    assert collected == ["ERROR alpha\n", "ERROR beta\n"]


def test_no_new_data_returns_empty(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("INFO only\n")
    d = tmp_path / "ck"
    # Consume everything
    _run(str(log), None, d)
    # No new bytes appended
    results = _run(str(log), None, d)
    assert results == []
