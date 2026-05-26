"""Log rotation detection and file re-open support for logslice."""

import os
from typing import IO, Iterator, Optional


def file_inode(path: str) -> Optional[int]:
    """Return the inode number of *path*, or None if the file does not exist."""
    try:
        return os.stat(path).st_ino
    except OSError:
        return None


def file_size(path: str) -> int:
    """Return the current size of *path* in bytes, or 0 if it does not exist."""
    try:
        return os.stat(path).st_size
    except OSError:
        return 0


def has_rotated(path: str, known_inode: Optional[int]) -> bool:
    """Return True when the file at *path* has been rotated.

    Rotation is detected by comparing the current inode against
    *known_inode*.  A missing file is also treated as rotated so that
    callers can wait for the new file to appear.
    """
    if known_inode is None:
        return False
    current = file_inode(path)
    return current is None or current != known_inode


def has_truncated(path: str, known_size: int) -> bool:
    """Return True when *path* is smaller than *known_size* (log truncation)."""
    return file_size(path) < known_size


def iter_with_reopen(
    path: str,
    poll_interval: float = 0.25,
    max_polls: Optional[int] = None,
) -> Iterator[str]:
    """Yield lines from *path*, re-opening the file when rotation is detected.

    Parameters
    ----------
    path:
        Path to the log file to follow.
    poll_interval:
        Seconds to sleep between polls when no new data is available.
        Not used in this pure-logic implementation but kept for API
        compatibility with real tail-follow usage.
    max_polls:
        Maximum number of empty polls before stopping.  Useful in tests
        and batch contexts.  ``None`` means run forever (not used in
        unit tests).
    """
    import time

    known_inode: Optional[int] = None
    fh: Optional[IO[str]] = None
    polls = 0

    try:
        while True:
            if fh is None:
                if not os.path.exists(path):
                    if max_polls is not None and polls >= max_polls:
                        break
                    polls += 1
                    time.sleep(poll_interval)
                    continue
                fh = open(path, "r", encoding="utf-8", errors="replace")
                known_inode = file_inode(path)
                polls = 0

            line = fh.readline()
            if line:
                polls = 0
                yield line
                continue

            # No new data — check for rotation or truncation
            if has_rotated(path, known_inode) or has_truncated(
                path, fh.tell()
            ):
                fh.close()
                fh = None
                known_inode = None
                continue

            if max_polls is not None and polls >= max_polls:
                break
            polls += 1
            time.sleep(poll_interval)
    finally:
        if fh is not None:
            fh.close()
