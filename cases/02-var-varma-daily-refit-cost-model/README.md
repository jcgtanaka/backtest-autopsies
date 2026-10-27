> **NOTICE**
>
> **Warning:** survivorship bias. The stock universe in this case is a list of companies that survived to today. Companies that failed, were delisted or were acquired are missing, so the equity results are likely optimistic. Read them as an upper bound.
>
> **Purpose:** This case shares the strategy logic so you can re-run it on survivorship-free data, for example point-in-time index membership that includes delisted companies and their full price history. Swap the universe and the price loader, keep the rules, and compare the results. The published numbers are for the survivor universe only and must not be read as a realistic estimate.

# Backtest Autopsy #2: daily-refit VAR on 19 assets, no forecasting skill, then costs

Tags: [no signal](../../docs/taxonomy.md#no-signal) (main), [cost model](../../docs/taxonomy.md#cost-model) (secondary)

**Verdict:** over 125 out-of-sample days on 100,000 USD of illustrative equity the gross P&L was -449 USD (-0.45%), costs 6,797 USD (6.8%), net -7,246 USD (annualised Sharpe -2.5). The forecast has no skill (directional hit rate 51.2%, 95% interval 49.2% to 53.3%; out-of-sample R-squared -0.049 vs a zero forecast), so gross is about zero; costs then make it a certain loss.

Outputs below come from a run on real data (not redistributed). The synthetic mode (`AUTOPSY_SYNTHETIC=1`) runs the pipeline end to end on fake data and will NOT reproduce the failure.

**Initial equity.** The initial equity of 100,000 USD is an illustrative assumption; see the capital sweep (section 9.4 of the notebook) for 5,000 to 250,000 USD. The values below are the starting point for this case. Change them and re-run the test to see whether the verdict holds.

## Hypothesis
The 19 daily return series of FX, gold, crypto and equities are linearly interdependent through time. A joint VAR refit every day on a trailing window should capture lead-lag structure and give a next-day forecast whose sign is tradable.

## Data
Daily closes built from three raw sources (broker 1-minute bid/ask for FX and gold, 1-minute trades for two coins, public daily equity closes), inner-joined on common sessions. Key `(date, asset)`. See `data_schema.md`. No vendor rows are published; the notebook prints schema checks only (no counts, dates or hashes of the input).

## Method
Log returns; VAR(p), p = 1..5, refit on the largest trailing window tier (500 to 2,000 rows) that fits, order chosen by AIC; the sign of the one-step forecast sets an equal-notional long/short position (coins long-only, crypto cap), costs charged per order by asset class (public broker fee formulas plus slippage assumptions); 125 out-of-sample days of daily refits. A separate time-capped probe measures why the VARMA variant was abandoned. Full metrics table and about 25 plots in the notebook.

## Result
Gross -449 USD, costs 6,797 USD, net -7,246 USD. Daily turnover about 87% of equity (about 18 orders a day). Costs by class: FX 1,666 USD, crypto 2,898 USD, equity 2,224 USD, gold 10 USD.

## Killing test
(1) Label-permutation of the forecast days: share of shuffled forecasts with a gross P&L at least as good as the actual one is 0.47, so the gross result is indistinguishable from luck. (2) Cost sweep: break-even multiple -0.066, so no cost level is profitable. Forecast skill: out-of-sample R-squared -0.049 (zero forecast) and -0.043 (trailing mean), rank IC 0.024 (t = 0.88).

## Capital sweep (section 9.4 of the notebook)
Only the initial equity changes (same universe, model, costs and 126-day window; nothing retuned). Fixed share = per-order minimum tickets (flat FX commission, crypto and equity minimums) as a share of cost.

| equity (USD) | gross USD | cost USD | cost % equity | net USD (return) | net Sharpe | max DD | fixed share of cost | cost bp of traded |
|---|---|---|---|---|---|---|---|---|
| 5,000 | 6 | 2,397 | 47.9% | -2,391 (-47.8%) | -20.2 | -47.7% | 94% | 56.5 |
| 10,000 | -18 | 2,575 | 25.8% | -2,594 (-25.9%) | -9.8 | -26.0% | 88% | 26.7 |
| 25,000 | -92 | 3,172 | 12.7% | -3,264 (-13.1%) | -4.6 | -14.3% | 64% | 12.3 |
| 50,000 | -211 | 4,377 | 8.8% | -4,588 (-9.2%) | -3.2 | -11.1% | 46% | 8.3 |
| 100,000 | -449 | 6,797 | 6.8% | -7,246 (-7.2%) | -2.5 | -9.6% | 29% | 6.4 |
| 250,000 | -1,161 | 14,159 | 5.7% | -15,320 (-6.1%) | -2.1 | -8.7% | 13% | 5.3 |

What scales: dollar notional per slot and all proportional costs. What does not: per-order minimum tickets, so they dominate cost at small equity (94% at 5,000 USD) and fade at large equity (13% at 250,000 USD). The proportional part (about 5 bp of traded notional at turnover of roughly 107 times equity over the window) does not dilute, so net stays negative at every level. The reading changes with capital (ticket size vs turnover times spread); the verdict (no skill, then cost) does not.

## Lesson
Measure forecast skill and the implied turnover before the backtest P&L, and test the cost at the ticket size you will actually trade.

## What I would do differently
- Test skill (hit rate, out-of-sample R-squared, rank IC) before building the execution model.
- Size from a risk budget with a no-trade band, not equal notional per slot with idle capital.
- Reduce dimensionality (shrinkage or low-rank VAR) and refit less often.
- Put all series on a common clock before estimating cross-asset lead-lag.

## Implementation notes
The published code does the following. It is a starting point: change the universe, parameters or cost model and re-run the test.
1. **Universe.** Six FX majors, spot gold, two coins and ten large-cap equities, in an interleaved column order. The equities are downloaded by the notebook with `yfinance` (unadjusted close).
2. **Data.** Raw files are read from `AUTOPSY_DATA_DIR` (names in `data_schema.md`). No absolute paths are used.
3. **Capital.** 100,000 USD for illustration, with a capital sweep from 5,000 to 250,000 USD.
4. **Costs.** The broker fee formulas follow public schedules; the slippage assumptions are stated in the notebook.
5. **Instrumentation.** The loop records per-asset P&L and cost, commission vs spread/slippage, the fixed part of each order's cost, traded notional, and the forecast and realised vectors.
6. **Fitting.** With `max_q = 0` the fit is closed-form OLS, so candidates are fit sequentially in the notebook. The VARMAX path is retained.
7. **Reporting** uses the shared `autopsy_common.perf` metrics and plots. PDF and CSV writers and a command-line entry point are not included, and neither is a single-asset-exclusion diagnostic.

## Reproduce
1. `pip install -e ../..` and the `notebooks` extra (statsmodels, yfinance, pyarrow, matplotlib).
2. Put the raw files in a folder and `export AUTOPSY_DATA_DIR=<folder>` (see `data_schema.md`).
3. `jupyter nbconvert --to notebook --execute notebook.ipynb` (about 5 minutes including the VARMA probe and the capital sweep).
4. Synthetic mode: `AUTOPSY_SYNTHETIC=1 jupyter nbconvert --to notebook --execute notebook.ipynb`.

## Caveats
Six months of out-of-sample data cannot establish the sign of a small true edge. Sizing is a documented placeholder, not a validated rule. Educational material, not financial advice.
