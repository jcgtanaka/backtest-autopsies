import numpy as np
import pandas as pd
import pytest

from autopsy_common.perf import (
    drawdown_series,
    longest_drawdown_duration,
    monthly_returns,
    performance_summary,
    rolling_sharpe,
    rolling_vol,
    yearly_returns,
)


def _idx(n, start="2020-01-01"):
    return pd.bdate_range(start, periods=n)


def test_drawdown_series_known_values():
    r = pd.Series([0.1, -0.5, 0.0, 1.0], index=_idx(4))
    dd = drawdown_series(r)
    assert dd.iloc[0] == pytest.approx(0.0)
    assert dd.iloc[1] == pytest.approx(-0.5)
    assert dd.iloc[2] == pytest.approx(-0.5)
    assert dd.iloc[3] == pytest.approx(0.1 * 0 + (1.1 * 0.5 * 2.0) / 1.1 - 1.0)


def test_longest_drawdown_duration_counts_periods_below_peak():
    r = pd.Series([0.1, -0.1, 0.0, 0.0, 0.2, 0.01], index=_idx(6))
    assert longest_drawdown_duration(r) == 3  # three consecutive rows below the prior peak
    assert longest_drawdown_duration(pd.Series([0.01, 0.01, 0.01])) == 0


def test_monthly_and_yearly_returns_compound():
    idx = pd.to_datetime(["2020-01-15", "2020-01-20", "2020-02-03", "2021-01-04"])
    r = pd.Series([0.10, 0.10, -0.05, 0.02], index=idx)
    m = monthly_returns(r)
    assert m.loc["2020-01"] == pytest.approx(1.1 * 1.1 - 1.0)
    assert len(m) == 3
    y = yearly_returns(r)
    assert y.loc[2020] == pytest.approx(1.1 * 1.1 * 0.95 - 1.0)
    assert y.loc[2021] == pytest.approx(0.02)


def test_performance_summary_constant_gain_and_keys():
    r = pd.Series([0.01, -0.005] * 126, index=_idx(252))
    s = performance_summary(r, periods_per_year=252)
    for k in ["total_return", "cagr", "ann_vol", "sharpe", "sortino", "calmar", "max_drawdown",
              "max_drawdown_duration", "hit_rate", "profit_factor", "avg_win", "avg_loss",
              "win_loss_ratio", "skew", "kurtosis", "var_95", "cvar_95", "best_period", "worst_period",
              "best_month", "worst_month", "n_periods"]:
        assert k in s.index, k
    assert s["hit_rate"] == pytest.approx(0.5)
    assert s["profit_factor"] == pytest.approx(0.01 / 0.005)
    assert s["avg_win"] == pytest.approx(0.01)
    assert s["avg_loss"] == pytest.approx(-0.005)
    assert s["total_return"] == pytest.approx((1.01 * 0.995) ** 126 - 1.0)
    assert s["max_drawdown"] == pytest.approx(-0.005, abs=1e-9)


def test_performance_summary_gross_net_turnover_exposure_benchmark():
    idx = _idx(100)
    rng = np.random.default_rng(0)
    net = pd.Series(rng.normal(0.0004, 0.01, 100), index=idx)
    gross = net + 0.0003
    bench = pd.Series(rng.normal(0.0002, 0.01, 100), index=idx)
    turnover = pd.Series(0.5, index=idx)
    exposure = pd.Series(0.8, index=idx)
    s = performance_summary(net, gross_returns=gross, benchmark=bench, turnover=turnover, exposure=exposure)
    assert s["gross_total_return"] > s["total_return"]
    assert s["cost_drag_ann"] == pytest.approx((gross.mean() - net.mean()) * 252)
    assert s["avg_turnover"] == pytest.approx(0.5)
    assert s["avg_exposure"] == pytest.approx(0.8)
    assert "benchmark_sharpe" in s.index and "excess_total_return" in s.index
    assert "beta" in s.index and "correlation" in s.index


def test_performance_summary_degenerate_series_does_not_raise():
    s = performance_summary(pd.Series([0.0, 0.0, 0.0], index=_idx(3)))
    assert np.isnan(s["sharpe"])
    assert s["total_return"] == 0.0
    assert performance_summary(pd.Series(dtype=float))["n_periods"] == 0


def test_rolling_sharpe_and_vol_window():
    r = pd.Series(np.random.default_rng(1).normal(0.001, 0.01, 100), index=_idx(100))
    rs = rolling_sharpe(r, 30)
    rv = rolling_vol(r, 30)
    assert rs.iloc[:29].isna().all() and rs.iloc[29:].notna().all()
    assert rv.iloc[40] == pytest.approx(r.iloc[11:41].std() * np.sqrt(252))
