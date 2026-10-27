"""Extended performance metrics for a periodic return series.

Everything here is a pure function of the returns passed in. Returns are simple
(arithmetic) per-period returns on a DatetimeIndex. `periods_per_year` is always
explicit: there is no hidden 252.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def equity_curve(returns: pd.Series, start: float = 1.0) -> pd.Series:
    return start * (1.0 + pd.Series(returns).fillna(0.0)).cumprod()


def drawdown_series(returns: pd.Series) -> pd.Series:
    """Equity / running peak - 1, one value per period (<= 0)."""
    eq = equity_curve(returns)
    return eq / eq.cummax() - 1.0


def longest_drawdown_duration(returns: pd.Series) -> int:
    """Longest run of consecutive periods spent strictly below a prior peak."""
    below = (drawdown_series(returns) < -1e-12).to_numpy()
    longest = run = 0
    for flag in below:
        run = run + 1 if flag else 0
        longest = max(longest, run)
    return int(longest)


def _compound(r: pd.Series) -> float:
    return float((1.0 + r).prod() - 1.0)  # type: ignore[operator, arg-type]


def monthly_returns(returns: pd.Series) -> pd.Series:
    """Compounded return per calendar month, indexed by month period."""
    r = pd.Series(returns).dropna()
    if r.empty:
        return pd.Series(dtype=float)
    return r.groupby(r.index.to_period("M")).apply(_compound)


def yearly_returns(returns: pd.Series) -> pd.Series:
    r = pd.Series(returns).dropna()
    if r.empty:
        return pd.Series(dtype=float)
    return r.groupby(r.index.year).apply(_compound)


def rolling_sharpe(returns: pd.Series, window: int, periods_per_year: int = 252) -> pd.Series:
    r = pd.Series(returns)
    sd = r.rolling(window).std()
    return (r.rolling(window).mean() / sd.where(sd > 1e-12)) * np.sqrt(periods_per_year)


def rolling_vol(returns: pd.Series, window: int, periods_per_year: int = 252) -> pd.Series:
    return pd.Series(returns).rolling(window).std() * np.sqrt(periods_per_year)


def _sharpe(r: pd.Series, ppy: int, rf: float = 0.0) -> float:
    sd = r.std()
    if len(r) < 2 or not np.isfinite(sd) or sd < 1e-12:
        return float("nan")
    return float((r.mean() - rf / ppy) / sd * np.sqrt(ppy))


def performance_summary(
    returns: pd.Series,
    periods_per_year: int = 252,
    risk_free: float = 0.0,
    gross_returns: pd.Series | None = None,
    benchmark: pd.Series | None = None,
    turnover: pd.Series | None = None,
    exposure: pd.Series | None = None,
    confidence: float = 0.95,
) -> pd.Series:
    """One labelled column of metrics. `returns` are the net returns.

    Optional extras: `gross_returns` adds gross total return and annualised
    cost drag; `benchmark` adds benchmark Sharpe, excess return, beta,
    correlation and annualised alpha; `turnover` / `exposure` add their means.
    """
    r = pd.Series(returns).dropna().astype(float)
    n = len(r)
    out: dict = {"n_periods": n}
    if n == 0:
        return pd.Series(out)
    ppy = periods_per_year
    eq = (1.0 + r).cumprod()
    total = float(eq.iloc[-1] - 1.0)
    years = n / ppy
    cagr = float(eq.iloc[-1] ** (1.0 / years) - 1.0) if eq.iloc[-1] > 0 else float("nan")
    ann_vol = float(r.std() * np.sqrt(ppy)) if n > 1 else float("nan")
    dd = drawdown_series(r)
    max_dd = float(dd.min())
    downside = r[r < 0]
    dsd = float(downside.std()) if len(downside) > 1 else float("nan")
    wins, losses = r[r > 0], r[r < 0]
    avg_win = float(wins.mean()) if len(wins) else float("nan")
    avg_loss = float(losses.mean()) if len(losses) else float("nan")
    var = float(r.quantile(1.0 - confidence))
    tail = r[r <= var]
    monthly = monthly_returns(r)
    out.update({
        "total_return": total,
        "cagr": cagr,
        "ann_vol": ann_vol,
        "sharpe": _sharpe(r, ppy, risk_free),
        "sortino": float(r.mean() / dsd * np.sqrt(ppy)) if np.isfinite(dsd) and dsd > 1e-12 else float("nan"),
        "calmar": float(cagr / abs(max_dd)) if max_dd < 0 and np.isfinite(cagr) else float("nan"),
        "max_drawdown": max_dd,
        "max_drawdown_duration": longest_drawdown_duration(r),
        "hit_rate": float((r > 0).mean()),
        "profit_factor": float(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() != 0 else float("nan"),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "win_loss_ratio": float(avg_win / abs(avg_loss)) if np.isfinite(avg_win) and np.isfinite(avg_loss) and avg_loss != 0 else float("nan"),
        "skew": float(stats.skew(r)) if n > 2 and r.std() > 0 else float("nan"),
        "kurtosis": float(stats.kurtosis(r)) if n > 3 and r.std() > 0 else float("nan"),
        "var_95": var,
        "cvar_95": float(tail.mean()) if len(tail) else var,
        "best_period": float(r.max()),
        "worst_period": float(r.min()),
        "best_month": float(monthly.max()) if len(monthly) else float("nan"),
        "worst_month": float(monthly.min()) if len(monthly) else float("nan"),
    })
    if gross_returns is not None:
        g = pd.Series(gross_returns).reindex(r.index).fillna(0.0)
        out["gross_total_return"] = float((1.0 + g).prod() - 1.0)
        out["gross_sharpe"] = _sharpe(g, ppy, risk_free)
        out["cost_drag_ann"] = float((g.mean() - r.mean()) * ppy)
    if turnover is not None:
        out["avg_turnover"] = float(pd.Series(turnover).mean())
    if exposure is not None:
        out["avg_exposure"] = float(pd.Series(exposure).mean())
    if benchmark is not None:
        b = pd.Series(benchmark).reindex(r.index).fillna(0.0)
        out["benchmark_total_return"] = float((1.0 + b).prod() - 1.0)
        out["benchmark_sharpe"] = _sharpe(b, ppy, risk_free)
        out["excess_total_return"] = total - out["benchmark_total_return"]
        var_b = b.var()
        out["beta"] = float(r.cov(b) / var_b) if var_b > 1e-18 else float("nan")
        out["correlation"] = float(r.corr(b)) if b.std() > 0 and r.std() > 0 else float("nan")
        out["alpha_ann"] = float((r.mean() - out["beta"] * b.mean()) * ppy) if np.isfinite(out["beta"]) else float("nan")
    return pd.Series(out)
