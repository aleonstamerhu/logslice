"""Line sampling utilities for logslice.

Provides reservoir sampling and rate-based sampling to reduce
output volume when working with very large log files.
"""

import random
from typing import Iterable, Iterator, List, Optional


def sample_by_rate(lines: Iterable[str], rate: float, seed: Optional[int] = None) -> Iterator[str]:
    """Yield each line with probability `rate` (0.0 < rate <= 1.0).

    Args:
        lines: Input lines to sample.
        rate: Probability of keeping each line (e.g. 0.1 keeps ~10%).
        seed: Optional random seed for reproducibility.

    Yields:
        Lines that pass the random sample check.

    Raises:
        ValueError: If rate is not in the range (0.0, 1.0].
    """
    if not (0.0 < rate <= 1.0):
        raise ValueError(f"rate must be in (0.0, 1.0], got {rate!r}")

    rng = random.Random(seed)
    for line in lines:
        if rng.random() < rate:
            yield line


def reservoir_sample(lines: Iterable[str], count: int, seed: Optional[int] = None) -> List[str]:
    """Return exactly `count` lines chosen uniformly at random (reservoir sampling).

    Args:
        lines: Input lines to sample from.
        count: Number of lines to return.  If the input has fewer lines
               than `count`, all lines are returned.
        seed: Optional random seed for reproducibility.

    Returns:
        A list of sampled lines (order matches their original positions).

    Raises:
        ValueError: If count is negative.
    """
    if count < 0:
        raise ValueError(f"count must be >= 0, got {count!r}")

    rng = random.Random(seed)
    reservoir: List[str] = []

    for i, line in enumerate(lines):
        if i < count:
            reservoir.append(line)
        else:
            j = rng.randint(0, i)
            if j < count:
                reservoir[j] = line

    return reservoir


def every_nth(lines: Iterable[str], n: int) -> Iterator[str]:
    """Yield every n-th line (1-indexed: lines 1, n+1, 2n+1, …).

    Args:
        lines: Input lines.
        n: Step size.  Must be >= 1.

    Yields:
        Every n-th line.

    Raises:
        ValueError: If n < 1.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n!r}")

    for i, line in enumerate(lines):
        if i % n == 0:
            yield line
