"""Ruin checks for a USD equity path: did the account cross a floor, and when."""
from __future__ import annotations

from typing import Any

import pandas as pd


def ruin_report(equity: pd.Series, floor: float = 0.0) -> dict[str, Any]:
    """Summary of how an equity path relates to a floor (default zero).

    The floor is inclusive: a value equal to the floor counts as at or below it.
    `first_breach_position` is the zero-based row of the first value at or below
    the floor and `first_breach_label` its index label; both are None when the
    path never touches the floor.
    """
    eq = pd.Series(equity).astype(float)
    below = (eq <= floor).to_numpy()
    n_below = int(below.sum())
    if n_below:
        pos = int(below.argmax())
        label = eq.index[pos]
    else:
        pos, label = None, None
    return {
        "breached": bool(n_below > 0),
        "first_breach_position": pos,
        "first_breach_label": label,
        "min_equity": float(eq.min()) if len(eq) else float("nan"),
        "periods_at_or_below_floor": n_below,
        "share_at_or_below_floor": float(n_below / len(eq)) if len(eq) else float("nan"),
    }


def floor_equity_path(equity: pd.Series, floor: float = 0.0) -> pd.Series:
    """Equity if trading stopped at the first breach: every value from the first
    one at or below `floor` onward is set to `floor`. A path that never touches
    the floor is returned unchanged."""
    eq = pd.Series(equity).astype(float).copy()
    rep = ruin_report(eq, floor)
    if rep["breached"]:
        eq.iloc[rep["first_breach_position"]:] = floor
    return eq
