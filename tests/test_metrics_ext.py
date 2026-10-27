import numpy as np
import pandas as pd
import pytest

from autopsy_common.metrics import (
    alpha_beta_regression,
    bootstrap_corr_ci,
    bootstrap_mean_ci,
    cross_sectional_rank_ic,
)


def _idx(n, start="2020-01-01"):
    return pd.bdate_range(start, periods=n)


def test_bootstrap_mean_ci_constant_series_collapses_and_is_seeded():
    r = bootstrap_mean_ci(pd.Series([0.01] * 50), n_boot=200, seed=1)
    assert r["lo"] == pytest.approx(0.01) and r["hi"] == pytest.approx(0.01)
    x = pd.Series(np.random.default_rng(0).normal(0.0, 1.0, 300))
    a = bootstrap_mean_ci(x, n_boot=500, seed=3)
    b = bootstrap_mean_ci(x, n_boot=500, seed=3)
    assert a == b
    assert a["lo"] < a["mean"] < a["hi"]
    assert a["lo"] < 0.0 < a["hi"]  # zero-mean noise: the interval straddles zero


def test_bootstrap_mean_ci_too_few_points_returns_nan():
    r = bootstrap_mean_ci(pd.Series([0.1, 0.2]), n_boot=100, seed=0, min_obs=20)
    assert np.isnan(r["lo"]) and np.isnan(r["hi"])


def test_bootstrap_mean_ci_level_widens_interval():
    x = pd.Series(np.random.default_rng(1).normal(0.0, 1.0, 200))
    narrow = bootstrap_mean_ci(x, n_boot=800, seed=0, level=0.5)
    wide = bootstrap_mean_ci(x, n_boot=800, seed=0, level=0.99)
    assert (wide["hi"] - wide["lo"]) > (narrow["hi"] - narrow["lo"])


def test_bootstrap_corr_ci_perfect_and_independent():
    rng = np.random.default_rng(0)
    x = pd.Series(rng.normal(size=400))
    perfect = bootstrap_corr_ci(x, 2.0 * x + 1.0, n_boot=300, seed=1, block=5)
    assert perfect["corr"] == pytest.approx(1.0)
    assert perfect["lo"] > 0.99
    y = pd.Series(rng.normal(size=400))
    indep = bootstrap_corr_ci(x, y, n_boot=500, seed=1, block=5)
    assert abs(indep["corr"]) < 0.25  # unrelated series: small sample correlation
    assert indep["lo"] <= indep["corr"] <= indep["hi"]
    assert 0.0 < indep["hi"] - indep["lo"] < 0.4


def test_bootstrap_corr_ci_rejects_misaligned_lengths():
    with pytest.raises(ValueError):
        bootstrap_corr_ci(pd.Series([1.0, 2.0, 3.0]), pd.Series([1.0, 2.0]), n_boot=10)


def test_cross_sectional_rank_ic_signs_and_missing_rows():
    idx = _idx(3)
    cols = list("abcde")
    scores = pd.DataFrame([[1, 2, 3, 4, 5], [1, 2, 3, 4, 5], [1, 1, 1, 1, 1]], index=idx, columns=cols, dtype=float)
    rets = pd.DataFrame([[10, 20, 30, 40, 50], [5, 4, 3, 2, 1], [1, 2, 3, 4, 5]], index=idx, columns=cols, dtype=float)
    ic = cross_sectional_rank_ic(scores, rets)
    assert ic.iloc[0] == pytest.approx(1.0)
    assert ic.iloc[1] == pytest.approx(-1.0)
    assert np.isnan(ic.iloc[2])  # a constant score row has no rank information


def test_cross_sectional_rank_ic_min_obs_and_alignment():
    idx = _idx(2)
    scores = pd.DataFrame({"a": [1.0, np.nan], "b": [2.0, np.nan], "c": [3.0, 1.0]}, index=idx)
    rets = pd.DataFrame({"a": [1.0, 1.0], "b": [2.0, 2.0], "c": [3.0, 3.0]}, index=idx)
    ic = cross_sectional_rank_ic(scores, rets, min_obs=3)
    assert ic.iloc[0] == pytest.approx(1.0)
    assert np.isnan(ic.iloc[1])  # only one valid pair on the second row


def test_alpha_beta_regression_recovers_known_line():
    rng = np.random.default_rng(2)
    b = pd.Series(rng.normal(0.0005, 0.01, 500), index=_idx(500))
    r = 0.5 * b + 0.001
    out = alpha_beta_regression(r, b, periods_per_year=252)
    assert out["beta"] == pytest.approx(0.5)
    assert out["alpha_per_period"] == pytest.approx(0.001)
    assert out["alpha_ann"] == pytest.approx(0.001 * 252)
    assert out["r_squared"] == pytest.approx(1.0)


def test_alpha_beta_regression_noise_gives_insignificant_alpha_and_tracking_error():
    rng = np.random.default_rng(3)
    b = pd.Series(rng.normal(0.0, 0.01, 800), index=_idx(800))
    r = pd.Series(rng.normal(0.0, 0.01, 800), index=b.index)
    out = alpha_beta_regression(r, b, periods_per_year=252)
    assert abs(out["t_alpha"]) < 3.0
    assert out["tracking_error_ann"] > 0.0
    assert np.isfinite(out["information_ratio"])
