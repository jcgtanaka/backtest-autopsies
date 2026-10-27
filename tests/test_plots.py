import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from autopsy_common import plots


@pytest.fixture()
def rets():
    idx = pd.bdate_range("2020-01-01", periods=300)
    return pd.Series(np.random.default_rng(3).normal(0.0003, 0.01, 300), index=idx)


@pytest.mark.parametrize("name", [
    "plot_equity", "plot_drawdown", "plot_rolling_risk", "plot_monthly_heatmap",
    "plot_return_distribution", "plot_yearly_bars",
])
def test_return_based_plots_return_figure(rets, name):
    fig = getattr(plots, name)(rets)
    assert isinstance(fig, plt.Figure) and len(fig.axes) >= 1
    plt.close(fig)


def test_equity_with_gross_and_benchmark(rets):
    fig = plots.plot_equity(rets, gross=rets + 0.0002, benchmark=rets * 0.5)
    labels = [ln.get_label() for ln in fig.axes[0].get_lines()]
    assert {"net", "gross", "benchmark"} <= set(labels)
    plt.close(fig)


def test_exposure_turnover_and_cost_and_bar(rets):
    fig = plots.plot_exposure_turnover(pd.Series(0.5, index=rets.index), pd.Series(0.1, index=rets.index))
    assert len(fig.axes) == 2
    plt.close(fig)
    costs = pd.DataFrame({"commission": [1.0, 2.0], "spread": [0.5, 0.2]},
                         index=pd.to_datetime(["2020-01-31", "2020-02-29"]))
    fig = plots.plot_cost_decomposition(costs)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
    fig = plots.plot_bar_contribution(pd.Series({"a": 1.0, "b": -2.0}), title="x")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_heatmap_handles_short_series():
    r = pd.Series([0.01, -0.01], index=pd.to_datetime(["2020-01-02", "2020-01-03"]))
    fig = plots.plot_monthly_heatmap(r)
    plt.close(fig)
