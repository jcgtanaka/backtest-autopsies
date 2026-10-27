"""Synthetic daily OHLCV panel, same schema as the real daily bars used by the cases.

Prices are a driftless random walk with volatility clustering and no
predictability, so a strategy run on it should find no edge. Values are
rounded so nothing resembles real market data.
"""
from __future__ import annotations

from typing import Dict, Optional, Sequence

import numpy as np
import pandas as pd

PANEL_KEY = ["date", "asset"]
PANEL_SCHEMA: Dict[str, str] = {
    "date": "datetime",
    "asset": "string",
    "asset_class": "string",
    "open": "float64",
    "high": "float64",
    "low": "float64",
    "close": "float64",
    "volume": "int64",
    "spread": "float64",
}


def synthetic_daily_panel(
    assets: Sequence[str],
    n_days: int,
    seed: int = 7,
    start: str = "2018-01-01",
    asset_classes: Optional[Dict[str, str]] = None,
    daily_vol: float = 0.008,
) -> pd.DataFrame:
    """Synthetic, same schema as the real data. len == len(assets) * n_days."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, periods=n_days)
    asset_classes = asset_classes or {}
    frames = []
    common = rng.normal(0.0, 0.3, n_days)  # shared shock, mild cross-asset correlation
    for a in assets:
        h = np.zeros(n_days)
        for t in range(1, n_days):  # AR(1) log-vol => volatility clustering
            h[t] = 0.97 * h[t - 1] + 0.15 * rng.normal()
        vol = daily_vol * np.exp(h)
        ret = vol * (rng.normal(size=n_days) + common)
        close = 100.0 * np.exp(np.cumsum(ret))
        prev_close = np.r_[100.0, close[:-1]]
        open_ = prev_close * (1.0 + 0.1 * vol * rng.normal(size=n_days))
        wick = np.abs(rng.normal(size=(n_days, 2))) * (vol * 0.5)[:, None]
        high = np.maximum(open_, close) * (1.0 + wick[:, 0])
        low = np.minimum(open_, close) * (1.0 - wick[:, 1])
        frames.append(pd.DataFrame({
            "date": dates,
            "asset": a,
            "asset_class": asset_classes.get(a, "generic"),
            "open": np.round(open_, 4),
            "high": np.round(high, 4),
            "low": np.round(low, 4),
            "close": np.round(close, 4),
            "volume": (rng.integers(10, 500, n_days) * 100).astype("int64"),
            "spread": np.round(close * 0.0002, 4),
        }))
    out = pd.concat(frames, ignore_index=True)
    # rounding can break high/low ordering by a hair: enforce it
    out["high"] = out[["high", "open", "close"]].max(axis=1)
    out["low"] = out[["low", "open", "close"]].min(axis=1)
    return out.sort_values(PANEL_KEY).reset_index(drop=True)
