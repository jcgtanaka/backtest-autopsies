"""Data entry point shared by the case notebooks.

AUTOPSY_SYNTHETIC=1 -> synthetic panel (no vendor data needed).
Otherwise            -> $AUTOPSY_DATA_DIR/daily_bars.parquet, built by the
                        reader's own download step (never shipped here).
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Dict, Optional, Sequence

import pandas as pd

from .schema import check_schema
from .synthetic import PANEL_KEY, synthetic_daily_panel


def use_synthetic() -> bool:
    return os.environ.get("AUTOPSY_SYNTHETIC", "") == "1"


def load_daily_panel(schema: Dict[str, str], assets: Sequence[str], n_days: int,
                     asset_classes: Optional[Dict[str, str]] = None, seed: int = 7) -> pd.DataFrame:
    """Return a panel restricted to the columns of `schema`, validated against it."""
    if use_synthetic():
        df = synthetic_daily_panel(assets, n_days, seed=seed, asset_classes=asset_classes)
    else:
        folder = os.environ.get("AUTOPSY_DATA_DIR")
        if not folder:
            raise RuntimeError("Set AUTOPSY_SYNTHETIC=1, or AUTOPSY_DATA_DIR to a folder holding "
                               "daily_bars.parquet built by the case download step.")
        df = pd.read_parquet(Path(folder) / "daily_bars.parquet")
        df = df.sort_values(PANEL_KEY).reset_index(drop=True)
    df = df[list(schema)]
    check_schema(df, schema, PANEL_KEY)
    return df


def cardinality_summary(df: pd.DataFrame, key_levels: Sequence[str] = ("date", "asset")) -> pd.Series:
    """Counts and date range only. Never returns values or asset names."""
    out: dict[str, object] = {f"distinct_{k}": int(df[k].nunique()) for k in key_levels}
    out["rows"] = len(df)
    out["date_min"] = str(df["date"].min().date())
    out["date_max"] = str(df["date"].max().date())
    return pd.Series(out)


def dataframe_fingerprint(df: pd.DataFrame) -> str:
    """SHA-256 over column names, logical dtypes and row-wise value hashes.

    Independent of column order, so two readers with the same data but a
    different column layout get the same hash. The hash identifies a dataset
    without revealing any value.
    """
    h = hashlib.sha256()
    for col in sorted(df.columns):
        h.update(str(col).encode())
        h.update(str(df[col].dtype).encode())
        h.update(pd.util.hash_pandas_object(df[col], index=False).to_numpy().tobytes())
    return h.hexdigest()
