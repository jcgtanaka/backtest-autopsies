"""Return-series metrics and overfitting diagnostics (CSCV PBO, deflated Sharpe)."""
from __future__ import annotations

from itertools import combinations
from typing import Dict

import numpy as np
import pandas as pd
from scipy import stats

EULER_GAMMA = 0.5772156649015329


def sharpe_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
    r = pd.Series(returns).dropna()
    sd = r.std()
    if len(r) < 2 or not np.isfinite(sd) or sd < 1e-12:
        return float("nan")
    return float(np.sqrt(periods_per_year) * r.mean() / sd)


def max_drawdown(returns: pd.Series) -> float:
    eq = (1.0 + pd.Series(returns).fillna(0.0)).cumprod()
    return float((eq / eq.cummax() - 1.0).min())


def cscv_pbo(returns: pd.DataFrame, n_blocks: int = 10) -> Dict[str, object]:
    """Probability of Backtest Overfitting via combinatorially symmetric CV.

    `returns` is a (time x trial) matrix. Split time into n_blocks; for every
    way of choosing half the blocks as "in-sample", pick the trial with the best
    Sharpe in-sample and record its relative rank out-of-sample. PBO is the
    share of splits where that winner ranks at or below the OOS median.
    """
    x = returns.fillna(0.0).to_numpy()
    blocks = np.array_split(np.arange(len(x)), n_blocks)
    cnt = np.array([len(b) for b in blocks], dtype=float)
    s1 = np.array([x[b].sum(axis=0) for b in blocks])
    s2 = np.array([(x[b] ** 2).sum(axis=0) for b in blocks])

    def sharpe(idx):
        n = cnt[list(idx)].sum()
        m = s1[list(idx)].sum(axis=0) / n
        v = s2[list(idx)].sum(axis=0) / n - m**2
        return m / np.sqrt(np.maximum(v, 1e-18))

    n_trials = x.shape[1]
    logit_list: list[float] = []
    for ins in combinations(range(n_blocks), n_blocks // 2):
        oos = [b for b in range(n_blocks) if b not in ins]
        best = int(np.argmax(sharpe(ins)))
        oos_sr = sharpe(oos)
        rank = (oos_sr < oos_sr[best]).sum() + 1  # 1..N, N = best
        omega = rank / (n_trials + 1)
        logit_list.append(float(np.log(omega / (1.0 - omega))))
    logits = np.array(logit_list)
    return {"pbo": float((logits <= 0).mean()), "n_splits": len(logits), "logits": logits}


def deflated_sharpe_probability(returns: pd.Series, n_trials: int, trial_sharpe_std: float) -> float:
    """Bailey / Lopez de Prado deflated Sharpe: probability that the true Sharpe
    is positive after accounting for the best-of-N selection. Sharpe values are
    per-period (not annualised); `trial_sharpe_std` is the cross-trial standard
    deviation of per-period Sharpe ratios."""
    r = pd.Series(returns).dropna()
    t = len(r)
    sd = r.std()
    if t < 10 or sd < 1e-12:
        return float("nan")
    sr = r.mean() / sd
    skew, kurt = stats.skew(r), stats.kurtosis(r, fisher=False)
    if n_trials > 1:
        sr0 = trial_sharpe_std * (
            (1 - EULER_GAMMA) * stats.norm.ppf(1 - 1.0 / n_trials)
            + EULER_GAMMA * stats.norm.ppf(1 - 1.0 / (n_trials * np.e))
        )
    else:
        sr0 = 0.0
    denom = np.sqrt(max(1 - skew * sr + (kurt - 1) / 4.0 * sr**2, 1e-12))
    return float(stats.norm.cdf((sr - sr0) * np.sqrt(t - 1) / denom))


def block_bootstrap_sharpe(returns: pd.Series, block: int = 10, n_boot: int = 1000,
                           seed: int = 0, periods_per_year: int = 252) -> Dict[str, float]:
    """Moving-block bootstrap of the annualised Sharpe: 5th/95th percentile and the
    share of resamples with Sharpe > 0. Blocks preserve short-range dependence."""
    r = pd.Series(returns).dropna().to_numpy()
    n = len(r)
    if n < 2 * block:
        return {"lo": float("nan"), "hi": float("nan"), "share_positive": float("nan")}
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    srs = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, n - block + 1, n_blocks)
        x = np.concatenate([r[s:s + block] for s in starts])[:n]
        sd = x.std(ddof=1)
        srs[b] = np.sqrt(periods_per_year) * x.mean() / sd if sd > 1e-12 else np.nan
    return {"lo": float(np.nanpercentile(srs, 5)), "hi": float(np.nanpercentile(srs, 95)),
            "share_positive": float(np.nanmean(srs > 0))}


def bootstrap_mean_ci(values: pd.Series, n_boot: int = 2000, seed: int = 0, level: float = 0.95,
                      min_obs: int = 20) -> Dict[str, float]:
    """Seeded iid bootstrap interval for the mean of `values`.

    Returns `mean`, `lo` and `hi` (the central `level` interval). With fewer
    than `min_obs` observations the interval is NaN rather than misleading.
    """
    x = pd.Series(values).dropna().to_numpy(dtype=float)
    n = len(x)
    if n < max(min_obs, 2):
        return {"mean": float(x.mean()) if n else float("nan"), "lo": float("nan"), "hi": float("nan")}
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, n, size=(n_boot, n))].mean(axis=1)
    tail = (1.0 - level) / 2.0
    return {"mean": float(x.mean()), "lo": float(np.quantile(means, tail)), "hi": float(np.quantile(means, 1.0 - tail))}


def bootstrap_corr_ci(x: pd.Series, y: pd.Series, n_boot: int = 1000, seed: int = 0, block: int = 1,
                      level: float = 0.90) -> Dict[str, float]:
    """Seeded moving-block bootstrap interval for the Pearson correlation of two
    aligned series (pairs are resampled together, in blocks of `block` rows)."""
    a = pd.Series(x).to_numpy(dtype=float)
    b = pd.Series(y).to_numpy(dtype=float)
    if len(a) != len(b):
        raise ValueError("x and y must have the same length")
    keep = np.isfinite(a) & np.isfinite(b)
    a, b = a[keep], b[keep]
    n = len(a)
    if n < 2 * max(block, 2):
        return {"corr": float("nan"), "lo": float("nan"), "hi": float("nan")}
    corr = float(np.corrcoef(a, b)[0, 1])
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    draws = np.empty(n_boot)
    for i in range(n_boot):
        starts = rng.integers(0, n - block + 1, n_blocks)
        idx = (starts[:, None] + np.arange(block)[None, :]).ravel()[:n]
        aa, bb = a[idx], b[idx]
        sa, sb = aa.std(), bb.std()
        draws[i] = np.corrcoef(aa, bb)[0, 1] if sa > 1e-15 and sb > 1e-15 else np.nan
    tail = (1.0 - level) / 2.0
    return {"corr": corr, "lo": float(np.nanquantile(draws, tail)), "hi": float(np.nanquantile(draws, 1.0 - tail))}


def cross_sectional_rank_ic(scores: pd.DataFrame, returns: pd.DataFrame, min_obs: int = 3) -> pd.Series:
    """Per-row Spearman correlation between a score matrix and a realised-return
    matrix (rows are dates, columns are assets). Rows with fewer than `min_obs`
    valid pairs, or with a constant score or return row, are NaN."""
    s, r = scores.align(returns, join="inner")
    out = {}
    for label in s.index:
        a, b = s.loc[label].to_numpy(dtype=float), r.loc[label].to_numpy(dtype=float)
        ok = np.isfinite(a) & np.isfinite(b)
        if ok.sum() < min_obs or np.ptp(a[ok]) == 0 or np.ptp(b[ok]) == 0:
            out[label] = np.nan
        else:
            out[label] = float(stats.spearmanr(a[ok], b[ok])[0])
    return pd.Series(out, dtype=float)


def alpha_beta_regression(returns: pd.Series, benchmark: pd.Series, periods_per_year: int = 252) -> Dict[str, float]:
    """OLS of strategy returns on benchmark returns (same periods).

    Returns the per-period and annualised alpha, beta, the t-statistic of alpha,
    R-squared, the annualised tracking error of (strategy - benchmark) and the
    information ratio (annualised mean active return over tracking error).
    """
    r, b = pd.Series(returns).align(pd.Series(benchmark), join="inner")
    keep = r.notna() & b.notna()
    r, b = r[keep].to_numpy(dtype=float), b[keep].to_numpy(dtype=float)
    n = len(r)
    nan = float("nan")
    if n < 3 or np.var(b) < 1e-18:
        return {"alpha_per_period": nan, "alpha_ann": nan, "beta": nan, "t_alpha": nan, "r_squared": nan,
                "tracking_error_ann": nan, "information_ratio": nan}
    beta = float(np.cov(r, b, ddof=1)[0, 1] / np.var(b, ddof=1))
    alpha = float(r.mean() - beta * b.mean())
    resid = r - alpha - beta * b
    dof = n - 2
    s2 = float((resid ** 2).sum() / dof)
    se_alpha = float(np.sqrt(s2 * (1.0 / n + b.mean() ** 2 / ((b - b.mean()) ** 2).sum())))
    ss_tot = float(((r - r.mean()) ** 2).sum())
    active = r - b
    te = float(active.std(ddof=1) * np.sqrt(periods_per_year))
    return {
        "alpha_per_period": alpha,
        "alpha_ann": alpha * periods_per_year,
        "beta": beta,
        "t_alpha": alpha / se_alpha if se_alpha > 1e-15 else (nan if abs(alpha) < 1e-15 else float("inf")),
        "r_squared": 1.0 - float((resid ** 2).sum()) / ss_tot if ss_tot > 1e-18 else nan,
        "tracking_error_ann": te,
        "information_ratio": float(active.mean() * periods_per_year / te) if te > 1e-15 else nan,
    }
