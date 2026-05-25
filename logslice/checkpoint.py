"""Checkpoint support for resumable log processing.

Allows saving and loading the last processed byte offset so that
repeated runs over growing log files only process new lines.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional


_DEFAULT_DIR = Path.home() / ".logslice" / "checkpoints"


def _checkpoint_path(source: str, checkpoint_dir: Path) -> Path:
    """Return the checkpoint file path for a given source."""
    safe_name = source.replace(os.sep, "_").replace(":", "_").strip("_")
    return checkpoint_dir / f"{safe_name}.json"


def load_offset(source: str, checkpoint_dir: Optional[Path] = None) -> int:
    """Load the saved byte offset for *source*.

    Returns 0 if no checkpoint exists.
    """
    directory = Path(checkpoint_dir) if checkpoint_dir else _DEFAULT_DIR
    path = _checkpoint_path(source, directory)
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text())
        return int(data.get("offset", 0))
    except (json.JSONDecodeError, ValueError, OSError):
        return 0


def save_offset(source: str, offset: int, checkpoint_dir: Optional[Path] = None) -> None:
    """Persist the byte *offset* reached for *source*."""
    directory = Path(checkpoint_dir) if checkpoint_dir else _DEFAULT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = _checkpoint_path(source, directory)
    path.write_text(json.dumps({"source": source, "offset": offset}))


def clear_checkpoint(source: str, checkpoint_dir: Optional[Path] = None) -> bool:
    """Delete the checkpoint for *source*.  Returns True if it existed."""
    directory = Path(checkpoint_dir) if checkpoint_dir else _DEFAULT_DIR
    path = _checkpoint_path(source, directory)
    if path.exists():
        path.unlink()
        return True
    return False


def iter_from_checkpoint(
    source: str,
    checkpoint_dir: Optional[Path] = None,
    update: bool = True,
):
    """Yield lines from *source* starting after the last saved offset.

    If *update* is True, the checkpoint is advanced after iteration.
    """
    offset = load_offset(source, checkpoint_dir)
    new_offset = offset
    with open(source, "rb") as fh:
        fh.seek(offset)
        for raw in fh:
            new_offset += len(raw)
            yield raw.decode(errors="replace")
    if update and new_offset != offset:
        save_offset(source, new_offset, checkpoint_dir)
