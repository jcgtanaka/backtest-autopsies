"""Generic capital-sweep driver. The strategy run stays in the notebook: the
caller passes a function that maps an initial equity to a dict of scalar
results, and only the initial equity changes between calls."""
from __future__ import annotations

from typing import Callable, Mapping, Sequence

import pandas as pd


def capital_sweep(run_fn: Callable[[float], Mapping[str, float]], capitals: Sequence[float]) -> pd.DataFrame:
    """Run `run_fn(capital)` for every capital in order; one row per capital,
    `capital` first."""
    caps = list(capitals)
    if not caps:
        raise ValueError("capitals must not be empty")
    if any(c <= 0 for c in caps):
        raise ValueError("capitals must be positive")
    rows = []
    for c in caps:
        res = dict(run_fn(float(c)))
        rows.append({"capital": c, **res})
    return pd.DataFrame(rows)


def scale_returns_to_equity(returns: pd.Series, capital: float) -> pd.Series:
    """USD equity path of a return-space strategy with no fixed fees: capital
    times the compounded return. Linear in capital by construction."""
    return capital * (1.0 + pd.Series(returns).fillna(0.0)).cumprod()
