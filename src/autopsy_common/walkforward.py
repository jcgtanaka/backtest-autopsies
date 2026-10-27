"""Purged / embargoed walk-forward window generator."""
from __future__ import annotations

from typing import Iterator, Optional, Tuple


def walk_forward_windows(
    n: int,
    min_train: int,
    step: int,
    purge: int,
    embargo: int = 0,
    train_span: Optional[int] = None,
) -> Iterator[Tuple[int, int, int, int]]:
    """Yield (train_start, train_end, test_start, test_end), half-open row ranges.

    A refit happens every `step` rows starting at row `min_train`.
    - train_end = refit - purge: the last training row r satisfies
      r + purge < refit, so a label that looks `purge` rows ahead never
      reaches the segment where predictions are used.
    - test_start = refit + embargo: skips rows whose causal features straddle
      the boundary.
    - train_span, if given, makes the training window rolling instead of
      expanding.
    """
    refit = min_train
    while refit < n:
        train_end = refit - purge
        if train_end > 0:
            train_start = 0 if train_span is None else max(0, train_end - train_span)
            test_start = refit + embargo
            test_end = min(refit + step, n)
            if test_start < test_end:
                yield (train_start, train_end, test_start, test_end)
        refit += step
