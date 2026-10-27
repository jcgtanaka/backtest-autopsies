import numpy as np
import pandas as pd
import pytest

from autopsy_common.regimes import run_length_table
from autopsy_common.ruin import floor_equity_path, ruin_report


def _idx(n, start="2020-01-01"):
    return pd.bdate_range(start, periods=n)


def test_run_length_table_one_row_per_maximal_run():
    s = pd.Series(["a", "a", "b", "a", "a", "a"], index=_idx(6))
    t = run_length_table(s)
    assert list(t["label"]) == ["a", "b", "a"]
    assert list(t["length"]) == [2, 1, 3]
    assert t.loc[0, "start"] == s.index[0] and t.loc[0, "end"] == s.index[1]
    assert t.loc[2, "start"] == s.index[3] and t.loc[2, "end"] == s.index[5]


def test_run_length_table_treats_missing_as_its_own_label_and_handles_empty():
    s = pd.Series(["a", None, None, "a"], index=_idx(4))
    t = run_length_table(s, missing_label="none")
    assert list(t["label"]) == ["a", "none", "a"]
    assert list(t["length"]) == [1, 2, 1]
    empty = run_length_table(pd.Series([], dtype=object))
    assert list(empty.columns) == ["label", "start", "end", "length"]
    assert len(empty) == 0


def test_run_length_table_lengths_sum_to_series_length():
    rng = np.random.default_rng(0)
    s = pd.Series(rng.choice(["x", "y", "z"], 200), index=_idx(200))
    assert run_length_table(s)["length"].sum() == 200


def test_ruin_report_detects_first_breach_and_depth():
    eq = pd.Series([100.0, 60.0, 5.0, -3.0, -10.0, 20.0], index=_idx(6))
    r = ruin_report(eq, floor=0.0)
    assert r["breached"] is True
    assert r["first_breach_position"] == 3
    assert r["first_breach_label"] == eq.index[3]
    assert r["min_equity"] == pytest.approx(-10.0)
    assert r["periods_at_or_below_floor"] == 2
    assert r["share_at_or_below_floor"] == pytest.approx(2 / 6)


def test_ruin_report_no_breach():
    eq = pd.Series([100.0, 90.0, 120.0], index=_idx(3))
    r = ruin_report(eq, floor=0.0)
    assert r["breached"] is False
    assert r["first_breach_position"] is None
    assert r["first_breach_label"] is None
    assert r["periods_at_or_below_floor"] == 0


def test_ruin_report_floor_is_inclusive_and_configurable():
    eq = pd.Series([100.0, 10.0, 50.0], index=_idx(3))
    assert ruin_report(eq, floor=10.0)["first_breach_position"] == 1
    assert ruin_report(eq, floor=9.99)["breached"] is False


def test_floor_equity_path_freezes_at_floor_after_first_breach():
    eq = pd.Series([100.0, 60.0, -3.0, -10.0, 20.0], index=_idx(5))
    out = floor_equity_path(eq, floor=0.0)
    assert list(out) == [100.0, 60.0, 0.0, 0.0, 0.0]
    # an unbreached path is returned unchanged
    ok = pd.Series([1.0, 2.0, 3.0], index=_idx(3))
    assert list(floor_equity_path(ok)) == [1.0, 2.0, 3.0]
