# Backtest Autopsy #1: random forest on future SMA direction

Tags: [proxy target](../../docs/taxonomy.md#proxy-target), cost model

**Verdict:** the model beat the mechanical baselines on label accuracy (pooled 68.4% vs 61.8% for "yesterday's return sign", a lift of +6.7 points), yet its pooled gross Sharpe on the traded return was +0.07 with a block-bootstrap 5th to 95th percentile of [-0.23, +0.40] and -0.18 after spread. On 100,000 USD of illustrative equity: gross 5,892 USD, costs 27,499 USD, net -21,606 USD over 5,838 days. The accuracy lift bought no detectable direction.

> **Scope.** A simplified implementation of the idea (random forest on the direction of a smoothed FX price), with the parameter values listed in the notebook settings. The verdict applies to the version tested.

Outputs below come from a run on real data (not redistributed). The synthetic mode (`AUTOPSY_SYNTHETIC=1`) runs the pipeline end to end on fake data and will NOT reproduce the failure; a single synthetic path can show a positive gross Sharpe by luck, so the synthetic run prints a multi-seed table.

**Initial equity.** The initial equity of 100,000 USD is an illustrative assumption; see the capital sweep section (section 9 of the notebook) for 5,000 to 250,000 USD.

## Hypothesis
A random forest can predict the direction of a smoothed price (next 5-day average vs today's 5-day average) from causal features, and trading that prediction should beat a plain moving-average trend rule.

## Data
Daily bars for six liquid FX pairs built from minute bid/ask quotes (labels anonymised to P1..P6); source: Interactive Brokers (FX bid/ask export); terms of use and redistribution rights are not verified. Key `(date, asset)`. See `data_schema.md`. No vendor rows are published; the notebook prints schema checks only (no counts, dates or hashes of the input).

## Method
Label `sign(mean(close[t+1..t+5]) - mean(close[t-4..t]))`; one random forest per pair; rolling walk-forward, refit every 21 rows, purge of 5 rows (the label reach) and a 1-row embargo; unit-notional equal-weight backtest paying the observed spread; baselines scored on the same dates. Metrics table (Sharpe, Sortino, Calmar, drawdown and duration, profit factor, VaR/CVaR, skew, kurtosis, gross vs net, cost drag, turnover, exposure, bootstrap interval) and about 20 plots in the notebook.

## Result
Pooled label accuracy: model 68.4%, trailing slope 57.9%, lag-1 sign 61.8%. Traded outcome: correlation of signal with next-day return +0.0026; gross Sharpe +0.07; net Sharpe -0.18; net total return -21.6%; maximum drawdown -28.6%.

## Killing test
Score the traded outcome, not the label: signal vs next-day return, block bootstrap of the gross Sharpe (share of resamples above zero 0.66), sign-permutation test (share of shuffles at least as good 0.40) and a cost sweep (net Sharpe crosses zero near 0.25x the observed spread).

## Lesson
Evaluate a model on the P&L-relevant target and compare label accuracy with a mechanical rule that uses only past prices.

## What I would do differently
- Define the target as the traded return from the start; report accuracy only relative to the mechanical baseline built from the same inputs.
- Make the gross-before-cost signal check the first gate before sizing or portfolio machinery.
- Count independent decisions: a 5-row overlapping label has far fewer independent observations than rows.

## Capital sweep (section 9)
Costs are strictly proportional (spread over price), there are no minimum tickets or lots, so every ratio is identical from 5,000 to 250,000 USD; only dollar amounts scale. The verdict does not change with capital.

## Reproduce
1. `pip install -e ../..` and the `notebooks` extra.
2. Put `daily_bars.parquet` (schema in `data_schema.md`) in a folder and `export AUTOPSY_DATA_DIR=<folder>`.
3. `jupyter nbconvert --to notebook --execute notebook.ipynb` (a few minutes; the random forests dominate).
4. Synthetic mode: `AUTOPSY_SYNTHETIC=1 jupyter nbconvert --to notebook --execute notebook.ipynb`.

## Caveats
Educational material, not financial advice. The values below are the starting point for this case. Change them and re-run the test to see whether the verdict holds.
