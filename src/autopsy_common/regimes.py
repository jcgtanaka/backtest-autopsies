"""Run-length summaries of a categorical state series (regime labels, signal states)."""
from __future__ import annotations

import pandas as pd

RUN_COLUMNS = ["label", "start", "end", "length"]


def run_length_table(labels: pd.Series, missing_label: str = "missing") -> pd.DataFrame:
    """One row per maximal run of identical consecutive labels.

    Columns: `label`, `start` and `end` (the first and last index value of the
    run) and `length` (number of rows). Missing labels form their own run under
    `missing_label`. The lengths always sum to `len(labels)`.
    """
    s = pd.Series(labels)
    if s.empty:
        return pd.DataFrame(columns=RUN_COLUMNS)
    state = s.astype(object).where(s.notna(), missing_label)
    block = (state != state.shift()).cumsum()
    rows = []
    for _, grp in state.groupby(block, sort=True):
        rows.append({"label": grp.iloc[0], "start": grp.index[0], "end": grp.index[-1], "length": len(grp)})
    return pd.DataFrame(rows, columns=RUN_COLUMNS)
