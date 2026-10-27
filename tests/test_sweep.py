import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import pytest

from autopsy_common.plots import plot_capital_sweep
from autopsy_common.sweep import capital_sweep, scale_returns_to_equity


def test_capital_sweep_collects_rows_in_order_and_adds_capital_column():
    calls = []

    def run(cap):
        calls.append(cap)
        return {"net_return": -0.1, "cost_share": 1000.0 / cap}

    df = capital_sweep(run, [5_000, 100_000, 10_000])
    assert calls == [5_000, 100_000, 10_000]
    assert list(df["capital"]) == [5_000, 100_000, 10_000]
    assert df.loc[0, "cost_share"] == pytest.approx(0.2)
    assert list(df.columns[:1]) == ["capital"]


def test_capital_sweep_rejects_non_positive_capital_and_empty_grid():
    with pytest.raises(ValueError):
        capital_sweep(lambda c: {}, [0.0, 1.0])
    with pytest.raises(ValueError):
        capital_sweep(lambda c: {}, [])


def test_scale_returns_to_equity_is_linear_in_capital():
    r = pd.Series([0.01, -0.02, 0.03])
    e1 = scale_returns_to_equity(r, 1_000.0)
    e2 = scale_returns_to_equity(r, 100_000.0)
    assert e1.iloc[0] == pytest.approx(1_010.0)
    assert (e2 / e1).round(9).eq(100.0).all()


def test_plot_capital_sweep_returns_figure_with_optional_panels():
    df = pd.DataFrame({"capital": [5_000, 25_000, 100_000], "net_return": [-0.3, -0.1, -0.07],
                       "cost_share": [0.5, 0.2, 0.07], "sharpe": [-5.0, -3.0, -2.0],
                       "max_drawdown": [-0.4, -0.2, -0.1],
                       "fixed_cost_usd": [2000.0, 1900.0, 1800.0], "proportional_cost_usd": [100.0, 900.0, 5000.0]})
    fig = plot_capital_sweep(df)
    assert isinstance(fig, plt.Figure) and len(fig.axes) >= 4
    plt.close(fig)
    fig = plot_capital_sweep(df.drop(columns=["fixed_cost_usd", "proportional_cost_usd"]))
    assert len(fig.axes) == 3
    plt.close(fig)
