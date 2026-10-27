import numpy as np
import pandas as pd
import pytest

from autopsy_common.metrics import (
    block_bootstrap_sharpe,
    cscv_pbo,
    deflated_sharpe_probability,
    max_drawdown,
    sharpe_ratio,
)
from autopsy_common.schema import check_schema
from autopsy_common.synthetic import PANEL_KEY, PANEL_SCHEMA, synthetic_daily_panel
from autopsy_common.walkforward import walk_forward_windows


def test_synthetic_panel_matches_schema_and_is_deterministic():
    a = synthetic_daily_panel(["A", "B"], n_days=30, seed=3)
    b = synthetic_daily_panel(["A", "B"], n_days=30, seed=3)
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == 60
    assert check_schema(a, PANEL_SCHEMA, PANEL_KEY) is True


def test_synthetic_panel_ohlc_consistent():
    p = synthetic_daily_panel(["A"], n_days=200, seed=1)
    assert (p["high"] >= p[["open", "close"]].max(axis=1)).all()
    assert (p["low"] <= p[["open", "close"]].min(axis=1)).all()


def test_check_schema_names_missing_column_and_wrong_dtype():
    p = synthetic_daily_panel(["A", "B"], n_days=5, seed=1)
    with pytest.raises(ValueError, match="Missing columns"):
        check_schema(p.drop(columns=["close"]), PANEL_SCHEMA, PANEL_KEY)
    bad = p.copy()
    bad["volume"] = bad["volume"].astype(float)
    with pytest.raises(ValueError, match="Wrong dtypes"):
        check_schema(bad, PANEL_SCHEMA, PANEL_KEY)
    dup = pd.concat([p, p.iloc[:1]]).sort_values(PANEL_KEY).reset_index(drop=True)
    with pytest.raises(ValueError, match="not unique"):
        check_schema(dup, PANEL_SCHEMA, PANEL_KEY)


def test_walk_forward_windows_purge_and_embargo():
    w = list(walk_forward_windows(n=100, min_train=40, step=20, purge=5, embargo=1))
    assert w[0] == (0, 35, 41, 60)
    for tr_s, tr_e, te_s, te_e in w:
        assert tr_e + 5 < te_s  # label reach of the last train row stays before the test segment
        assert te_s < te_e
    assert w[-1][3] == 100


def test_walk_forward_rolling_span():
    w = list(walk_forward_windows(n=100, min_train=40, step=20, purge=5, train_span=30))
    assert w[0][0] == 5 and w[0][1] == 35


def test_sharpe_and_drawdown_known_values():
    r = pd.Series([0.01, -0.01] * 50)
    assert sharpe_ratio(r) == pytest.approx(0.0, abs=1e-9)
    assert max_drawdown(pd.Series([0.1, -0.5, 0.0])) == pytest.approx(-0.5)
    assert np.isnan(sharpe_ratio(pd.Series([0.0, 0.0, 0.0])))


def test_cscv_pbo_noise_is_mid_and_edge_is_low():
    rng = np.random.default_rng(0)
    noise = pd.DataFrame(rng.normal(0, 0.01, (800, 30)))
    assert 0.25 < cscv_pbo(noise, n_blocks=10)["pbo"] < 0.75
    edge = noise.copy()
    edge[0] = edge[0] + 0.01
    assert cscv_pbo(edge, n_blocks=10)["pbo"] < 0.1


def test_deflated_sharpe_drops_with_more_trials():
    rng = np.random.default_rng(1)
    r = pd.Series(rng.normal(0.0005, 0.01, 1000))
    few = deflated_sharpe_probability(r, n_trials=2, trial_sharpe_std=0.05)
    many = deflated_sharpe_probability(r, n_trials=500, trial_sharpe_std=0.05)
    assert many < few


def test_block_bootstrap_interval_brackets_zero_for_noise_and_excludes_it_for_drift():
    rng = np.random.default_rng(2)
    noise = pd.Series(rng.normal(0, 0.01, 1000))
    ci = block_bootstrap_sharpe(noise, block=10, n_boot=300, seed=1)
    assert ci["lo"] < 0 < ci["hi"]
    drift = pd.Series(rng.normal(0.01, 0.01, 1000))
    assert block_bootstrap_sharpe(drift, block=10, n_boot=300, seed=1)["lo"] > 0
    assert np.isnan(block_bootstrap_sharpe(noise.iloc[:5], block=10)["lo"])


def test_load_daily_panel_synthetic_and_missing_dir(monkeypatch):
    from autopsy_common.data import cardinality_summary, load_daily_panel
    monkeypatch.setenv("AUTOPSY_SYNTHETIC", "1")
    schema = {k: PANEL_SCHEMA[k] for k in ["date", "asset", "close"]}
    df = load_daily_panel(schema, ["A", "B"], 10)
    assert list(df.columns) == ["date", "asset", "close"]
    card = cardinality_summary(df)
    assert card["rows"] == 20 and card["distinct_asset"] == 2
    monkeypatch.setenv("AUTOPSY_SYNTHETIC", "0")
    monkeypatch.delenv("AUTOPSY_DATA_DIR", raising=False)
    with pytest.raises(RuntimeError, match="AUTOPSY_DATA_DIR"):
        load_daily_panel(schema, ["A"], 10)


def test_dataframe_fingerprint_is_deterministic_and_content_sensitive():
    from autopsy_common.data import dataframe_fingerprint
    p = synthetic_daily_panel(["A", "B"], n_days=20, seed=2)
    assert dataframe_fingerprint(p) == dataframe_fingerprint(p.copy())
    changed = p.copy()
    changed.loc[3, "close"] = changed.loc[3, "close"] + 1.0
    assert dataframe_fingerprint(changed) != dataframe_fingerprint(p)
    assert len(dataframe_fingerprint(p)) == 64
    # column order does not matter, column names do
    assert dataframe_fingerprint(p[p.columns[::-1]]) == dataframe_fingerprint(p)
    assert dataframe_fingerprint(p.rename(columns={"close": "px"})) != dataframe_fingerprint(p)
