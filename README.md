# backtest-autopsies

Failed quant strategies, killed by named tests, with the number that proves it.

![ci](https://github.com/jcgtanaka/backtest-autopsies/actions/workflows/ci.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![licence](https://img.shields.io/badge/licence-MIT-green)

<!-- TO VERIFY: the CI badge URL only resolves once the repo exists on GitHub under this name and the workflow has run. -->

Case studies of failed quant strategies: purged CV, PBO, walk-forward,
multiple-testing and data-leakage diagnostics. Reproducible notebooks.

Each case is a starting point, not a finished answer. The logic is published so
you can change the rules, swap the data and check whether the verdict still
holds. A verdict applies to the version tested.

## The cases

Every number below comes from the case README and its executed notebook, at
the 100,000 USD illustrative-equity headline (a capital sweep from 5,000 to
250,000 USD is inside each case).

| # | Strategy idea | Failure mode | Killing test | Key number |
|---|---------------|--------------|--------------|------------|
| [1](cases/01-forex-ml-sma-direction/) | Random forest predicts the direction of a smoothed FX price | [proxy target](docs/taxonomy.md#proxy-target), cost model | Score the traded return, not the label: block bootstrap, sign permutation, cost sweep | Label accuracy 68.4% vs 61.8% baseline, but gross Sharpe +0.07 (5th to 95th pct [-0.23, +0.40]); net -21,606 USD |
| [2](cases/02-var-varma-daily-refit-cost-model/) | Daily-refit VAR on 19 assets, trade the forecast sign | [cost model](docs/taxonomy.md#cost-model) (no forecast skill first) | Hit rate and out-of-sample R-squared, label permutation, cost sweep | Hit rate 51.2%; gross -449 USD, costs 6,797 USD, net -7,246 USD in 125 days |
| [3](cases/03-forex-cusum-adf-regime/) | CUSUM trend detector plus rolling-ADF mean-reversion detector routing six FX pairs | [regime starvation](docs/taxonomy.md#regime-starvation), [cost model](docs/taxonomy.md#cost-model) | Count independent regime events, funnel, minimum detectable edge, episode bootstrap | 17 mean-reversion development trades in 11 episodes (smallest detectable edge about 32 bp per trade); baseline -37.9%, routing -27.4% net (mid-to-mid +7.4% and +6.6%) |
| [4](cases/04-forex-free-factor/) | Free spot factors, CFTC positioning and policy rates in a capped currency-neutral FX book | [no signal](docs/taxonomy.md#no-signal), [cost model](docs/taxonomy.md#cost-model) | Rank IC, hit-rate interval, day-shuffle permutation of the held weights, weekly low-turnover variant | Rank IC +0.013 (t = 1.32), hit rate 50.2%, permutation p = 0.87; gross -4.7%, net -10.9% (CAGR -1.63%, Sharpe -0.65) |
| [5](cases/05-sp500-top5-hrp/) | S&P 500 top-20 momentum to top-5 hierarchical risk parity, volatility-targeted (**stock-based: survivorship warning**) | [no edge vs benchmark](docs/taxonomy.md#no-edge-vs-benchmark) | Alpha against SPY and vol-targeted SPY, random-selection placebo, lookback sensitivity | CAGR -0.04% vs 14.2% for SPY and 11.0% for vol-targeted SPY; alpha -8.4% (t = -1.65); Sharpe at the 9th percentile of 100 random selections |
| [6](cases/06-crypto-equal-weight-minimum-ticket/) | Equal-weight five-coin crypto basket with a per-order minimum fee | [cost model](docs/taxonomy.md#cost-model) | Capital sweep with ruin check, fixed versus proportional cost, ruin floor | Daily rebalancing -36.4% (costs 18.2% of equity) vs monthly -14.2% (2.6%); equity below zero only for daily at 10,000 USD or less |

## Publication status

This repository publishes cases 01 to 06 now, with derived results only and no
vendor data values. Further cases are added after review.

## Who this is for, and what is not here

- For researchers and hiring teams who distrust backtests and want to see the
  test that killed an idea and the number behind it.
- Not here: no vendor data.
- Case 1 tests a random forest on the direction of a smoothed FX price, with the parameter values listed in its README. The verdict applies to the version tested.
  Cases 2 to 6 test the strategy logic described in each case README, with the values listed there (see "Implementation notes" in each case README).
  Case 5 is stock-based and carries a survivorship warning.

## Quickstart (synthetic mode)

Synthetic mode runs a case end to end on fake data. It does not reproduce the
published failure; the executed notebooks in the repo hold the real-data
results.

```
pip install -e ".[dev,notebooks]"
AUTOPSY_SYNTHETIC=1 jupyter nbconvert --to notebook --execute cases/01-forex-ml-sma-direction/notebook.ipynb --output-dir out
pytest -q
```

## Links

- [Failure taxonomy](docs/taxonomy.md)
- [Pre-backtest checklist](docs/pre_backtest_checklist.md)
- [Case template](docs/case_template.md)
- [Audit checklist](docs/audit_checklist.md)
- [Data licensing](DATA_LICENSING.md)
- [Changelog](CHANGELOG.md)

## How data is handled

No historical data file or raw row is committed. The repo publishes code,
executed results, schemas, a synthetic sample and counts or content hashes as
metadata. Readers obtain data under their own licence and point
`AUTOPSY_DATA_DIR` at it. Vendor terms have not been verified by the author;
see [DATA_LICENSING.md](DATA_LICENSING.md). `tools/publish_gate.py` blocks
raw-data-looking content in notebooks and markdown.

## Disclaimer

Educational material, not financial advice. Nothing here is a recommendation
to buy or sell any instrument. Results are historical, simplified and were
selected because they failed. The parameter values in each case are the starting point for that case: change them and re-run the test to see whether the verdict holds.

## Author

jcgtanaka.
