"""Causal daily price features shared by the cases. Every column at row t uses
data up to and including t only."""
from __future__ import annotations

import numpy as np
import pandas as pd


def price_features(bars: pd.DataFrame) -> pd.DataFrame:
    """`bars` is one asset's daily frame (columns close/high/low, optional
    volume), indexed by date. Windows are a starting point: change them and re-test."""
    close = bars["close"]
    ret1 = close.pct_change()
    f = pd.DataFrame(index=bars.index)
    f["ret_1d"] = ret1
    f["ret_3d"] = close.pct_change(3)
    f["ret_5d"] = close.pct_change(5)
    f["ret_20d"] = close.pct_change(20)
    f["mom_5_20"] = f["ret_5d"] - f["ret_20d"]
    f["rvol_10d"] = ret1.rolling(10).std()
    f["rvol_20d"] = ret1.rolling(20).std()
    f["vol_of_vol_20d"] = f["rvol_10d"].pct_change().rolling(20).std()
    f["ewma_vol"] = ret1.ewm(span=30, min_periods=30).std()
    f["vol_regime"] = f["ewma_vol"] / f["ewma_vol"].rolling(252, min_periods=60).median()
    f["range_frac"] = (bars["high"] - bars["low"]) / close
    f["trend_spread"] = close.rolling(5).mean() / close.rolling(20).mean() - 1.0
    f["zscore_10"] = (close - close.rolling(10).mean()) / close.rolling(10).std()
    delta = close.diff()
    gain = delta.clip(lower=0.0).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    loss = (-delta.clip(upper=0.0)).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    f["rsi_14"] = (100.0 - 100.0 / (1.0 + gain / loss.replace(0.0, np.nan))).fillna(50.0)
    if "volume" in bars:
        v = bars["volume"].astype(float)
        f["volume_z_20d"] = (v - v.rolling(20).mean()) / (v.rolling(20).std() + 1e-9)
    return f.replace([np.inf, -np.inf], np.nan)
