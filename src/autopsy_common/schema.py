"""Schema validation for a reader's own download or the synthetic sample."""
from __future__ import annotations

from typing import Dict, Sequence

import pandas as pd


def logical_dtype(series: pd.Series) -> str:
    """Pandas-version-independent dtype label: datetime, string, or numpy name."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_string_dtype(series) or series.dtype == object:
        return "string"
    return str(series.dtype)


def check_schema(df: pd.DataFrame, expected: Dict[str, str], key: Sequence[str]) -> bool:
    """Fail early, with a clear message, if columns, dtypes, key uniqueness or
    sort order do not match. Returns True when everything matches."""
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Re-run the download step.")
    wrong = {c: logical_dtype(df[c]) for c, t in expected.items() if logical_dtype(df[c]) != t}
    if wrong:
        raise ValueError(f"Wrong dtypes (got): {wrong}; expected {expected}")
    key = list(key)
    if df.duplicated(key).any():
        raise ValueError(f"Key {key} is not unique")
    if not df.sort_values(key).index.equals(df.index):
        raise ValueError(f"Data must be sorted by the key {key}")
    return True
