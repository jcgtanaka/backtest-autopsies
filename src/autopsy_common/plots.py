"""Matplotlib helpers for strategy-derived results. Every function takes pandas
objects computed by the case and returns a Figure; none of them read data."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from .perf import drawdown_series, equity_curve, monthly_returns, rolling_sharpe, rolling_vol, yearly_returns


def plot_equity(net: pd.Series, gross: pd.Series | None = None, benchmark: pd.Series | None = None,
                title: str = "Equity curve (start = 1.0)") -> plt.Figure:
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(equity_curve(net), label="net", lw=1.8)
    if gross is not None:
        ax.plot(equity_curve(gross), label="gross", lw=1.2, ls="--")
    if benchmark is not None:
        ax.plot(equity_curve(benchmark), label="benchmark", lw=1.0, color="grey")
    ax.axhline(1.0, color="k", lw=0.5)
    ax.set_title(title)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def plot_drawdown(returns: pd.Series, title: str = "Drawdown") -> plt.Figure:
    fig, ax = plt.subplots(figsize=(9, 3))
    dd = drawdown_series(returns)
    ax.fill_between(dd.index, dd.values, 0.0, color="firebrick", alpha=0.5)
    ax.set_title(title)
    ax.set_ylabel("drawdown")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def plot_rolling_risk(returns: pd.Series, window: int = 60, periods_per_year: int = 252,
                      title: str | None = None) -> plt.Figure:
    window = max(2, min(window, max(2, len(returns) // 2)))
    fig, axes = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
    axes[0].plot(rolling_sharpe(returns, window, periods_per_year))
    axes[0].axhline(0.0, color="k", lw=0.5)
    axes[0].set_ylabel("rolling Sharpe")
    axes[1].plot(rolling_vol(returns, window, periods_per_year), color="darkorange")
    axes[1].set_ylabel("rolling ann. vol")
    axes[0].set_title(title or f"Rolling {window}-period Sharpe and volatility")
    for a in axes:
        a.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def plot_monthly_heatmap(returns: pd.Series, title: str = "Monthly returns (%)") -> plt.Figure:
    m = monthly_returns(returns)
    fig, ax = plt.subplots(figsize=(9, 1.2 + 0.5 * max(1, m.index.year.nunique() if len(m) else 1)))
    if m.empty:
        ax.set_title(title)
        return fig
    table = pd.DataFrame({"year": m.index.year, "month": m.index.month, "r": m.values}).pivot(
        index="year", columns="month", values="r").reindex(columns=range(1, 13))
    lim = max(float(np.nanmax(np.abs(table.values))), 1e-9)
    im = ax.imshow(table.values * 100, aspect="auto", cmap="RdYlGn", vmin=-lim * 100, vmax=lim * 100)
    ax.set_xticks(range(12), ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    ax.set_yticks(range(len(table)), table.index.astype(str))
    for i in range(table.shape[0]):
        for j in range(12):
            v = table.values[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v * 100:.1f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title(title)
    fig.tight_layout()
    return fig


def plot_return_distribution(returns: pd.Series, title: str = "Return distribution vs normal",
                             bins: int = 40) -> plt.Figure:
    r = pd.Series(returns).dropna()
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    axes[0].hist(r, bins=bins, density=True, alpha=0.6, label="strategy")
    if len(r) > 2 and r.std() > 0:
        x = np.linspace(r.min(), r.max(), 200)
        axes[0].plot(x, stats.norm.pdf(x, r.mean(), r.std()), "k--", label="normal fit")
        stats.probplot(r, dist="norm", plot=axes[1])
    axes[0].legend()
    axes[0].set_title(title)
    axes[1].set_title("Normal Q-Q")
    fig.tight_layout()
    return fig


def plot_yearly_bars(returns: pd.Series, title: str = "Calendar-year returns (%)") -> plt.Figure:
    y = yearly_returns(returns) * 100
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(y.index.astype(str), y.values, color=np.where(y.values >= 0, "seagreen", "firebrick"))
    ax.axhline(0.0, color="k", lw=0.5)
    ax.set_title(title)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    return fig


def plot_exposure_turnover(exposure: pd.Series, turnover: pd.Series,
                           title: str = "Exposure and turnover") -> plt.Figure:
    fig, axes = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
    axes[0].plot(exposure, color="steelblue")
    axes[0].set_ylabel("exposure")
    axes[1].plot(turnover, color="purple")
    axes[1].set_ylabel("turnover")
    axes[0].set_title(title)
    for a in axes:
        a.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def plot_cost_decomposition(costs: pd.DataFrame, title: str = "Costs by component") -> plt.Figure:
    """`costs` is a (period x component) table of non-negative cost amounts."""
    fig, ax = plt.subplots(figsize=(9, 4))
    bottom = np.zeros(len(costs))
    x = np.arange(len(costs))
    for c in costs.columns:
        ax.bar(x, costs[c].values, bottom=bottom, label=str(c))
        bottom = bottom + costs[c].values
    labels = [str(i)[:7] if hasattr(i, "year") else str(i) for i in costs.index]
    ax.set_xticks(x, labels, rotation=45)
    ax.set_title(title)
    ax.legend()
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    return fig


def plot_bar_contribution(values: pd.Series, title: str, xlabel: str = "") -> plt.Figure:
    v = pd.Series(values).sort_values()
    fig, ax = plt.subplots(figsize=(7, 0.3 * len(v) + 1.5))
    ax.barh(v.index.astype(str), v.values, color=np.where(v.values >= 0, "seagreen", "firebrick"))
    ax.axvline(0.0, color="k", lw=0.5)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.grid(alpha=0.3, axis="x")
    fig.tight_layout()
    return fig


def plot_capital_sweep(sweep: pd.DataFrame, title: str = "Capital sweep (only initial equity changes)") -> plt.Figure:
    """Panels: net return and cost share vs capital; net Sharpe; max drawdown;
    and, when `fixed_cost_usd` and `proportional_cost_usd` are present, the cost
    split as a share of capital. Expects columns capital, net_return,
    cost_share, sharpe, max_drawdown."""
    has_split = {"fixed_cost_usd", "proportional_cost_usd"} <= set(sweep.columns)
    n = 4 if has_split else 3
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 3.6))
    x = sweep["capital"].astype(float)
    axes[0].plot(x, sweep["net_return"] * 100, marker="o", label="net return %")
    axes[0].plot(x, sweep["cost_share"] * 100, marker="s", label="cost % of capital")
    axes[0].axhline(0.0, color="k", lw=0.5)
    axes[0].set_title("Net return and cost vs capital")
    axes[0].legend()
    axes[1].plot(x, sweep["sharpe"], marker="o", color="darkorange")
    axes[1].axhline(0.0, color="k", lw=0.5)
    axes[1].set_title("Net Sharpe")
    axes[2].plot(x, sweep["max_drawdown"] * 100, marker="o", color="firebrick")
    axes[2].set_title("Max drawdown (%)")
    if has_split:
        cap = x.to_numpy()
        axes[3].bar(range(len(x)), sweep["fixed_cost_usd"] / cap * 100, label="fixed per-order (% of capital)")
        axes[3].bar(range(len(x)), sweep["proportional_cost_usd"] / cap * 100,
                    bottom=sweep["fixed_cost_usd"] / cap * 100, label="proportional (% of capital)")
        axes[3].set_xticks(range(len(x)), [f"{int(c / 1000)}k" for c in x])
        axes[3].set_title("Cost split")
        axes[3].legend(fontsize=7)
    for a in axes[:3]:
        a.set_xscale("log")
        a.set_xlabel("initial equity (USD, log)")
    fig.suptitle(title)
    fig.tight_layout()
    return fig
