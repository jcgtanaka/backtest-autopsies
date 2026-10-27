> **NOTICE**
>
> **Warning:** survivorship bias. The stock universe in this case is a list of companies that survived to today. Companies that failed, were delisted or were acquired are missing, so the equity results are likely optimistic. Read them as an upper bound. Membership is point-in-time from the constituents file, but yfinance lacks many delisted names, which drop out of the eligible set, and membership after the last historical date is backfilled with the current list.
>
> **Purpose:** This case shares the strategy logic so you can re-run it on survivorship-free data, for example point-in-time index membership that includes delisted companies and their full price history. Swap the universe and the price loader, keep the rules, and compare the results. The published numbers are for the survivor universe only and must not be read as a realistic estimate.

# Backtest Autopsy #5: S&P 500 top-20 momentum to top-5 hierarchical risk parity, no edge against the index

Tags: [no edge vs benchmark](../../docs/taxonomy.md#no-edge-vs-benchmark)

**Verdict:** on 100,000 USD of illustrative equity the strategy compounds at -0.04% a year (annualised Sharpe -0.15 over a 4.5% cash rate, maximum drawdown -43.1%, final value 99,689 USD) against 14.2% for buy-and-hold SPY (Sharpe 0.54, maximum drawdown -33.7%, 261,433 USD) and 11.0% for SPY volatility-targeted to the same 14% (Sharpe 0.50, maximum drawdown -21.0%, 213,357 USD). Regressed on SPY: alpha -8.1% a year (t = -1.63), beta 0.64; against the vol-targeted SPY alpha -8.4% (t = -1.65). The Sharpe is at the 9th percentile of 100 random-selection runs of the same engine.

Outputs below come from a run on real data (not redistributed). The synthetic mode (`AUTOPSY_SYNTHETIC=1`) runs the pipeline end to end on a synthetic stock panel and will NOT reproduce the failure.

**Initial equity.** The initial equity of 100,000 USD is an illustrative assumption; see the capital sweep (section 10 of the notebook) for 5,000 to 250,000 USD. The values below are the starting point for this case. Change them and re-run the test to see whether the verdict holds.

## Hypothesis
Ranking index members by six-month momentum, then letting Hierarchical Risk Parity pick and weight five of the top 20, with a volatility target, should beat holding the index.

## Data
Daily adjusted closes for the S&P 500 members plus SPY (free price source, downloaded by the reader) and a membership history (public GitHub history file, extended after its last snapshot). Keys `(date, ticker)` for membership and `date` for prices. See `data_schema.md`. No vendor rows are published; the notebook prints schema checks only.

## Method
Monthly rebalance (21 trading days): members at the date, 105-day momentum skipping the latest 21 days, top 20, HRP (Ward linkage, quasi-diagonalisation, recursive bisection), keep the five largest weights clipped to 5%-40%, scale to a 14% volatility target with a correlation-adaptive multiplier, idle cash at 4.5%, 3 basis points of cost. Two benchmarks: SPY and SPY vol-targeted to the same level. Placebo: the same engine with 20 names drawn at random. Full metrics table and fourteen plots in the notebook.

## Result
Section 6 table: see the verdict. The strategy beats SPY in 25% of calendar years and the vol-targeted SPY in 12%. Average turnover 74% of the book per rebalance; average gross exposure 0.76. Paired block bootstrap of the Sharpe difference (90%): [-1.13, -0.25] against SPY and [-1.09, -0.20] against the vol-targeted SPY.

## Killing test
Benchmark comparison and placebo (notebook sections 6 and 9). Alpha against the like-for-like benchmark is negative (t = -1.65); the placebo has mean CAGR 4.6% and mean Sharpe 0.09, with 91% of random runs at least as good as the strategy. Ten lookback and skip pairs give CAGRs from -0.04% to 9.5% (median 4.0%); none beats SPY, and the headline pair is the lowest. Survivorship measurement: members later removed have a price on 58% of rebalance dates against 94% for those still in the index; 95% of rebalance dates fall after the public membership file's last snapshot.

## Capital sweep (section 10 of the notebook)
Only the initial equity changes (nothing retuned). Headline cost model (3 basis points, proportional): every ratio is identical at every level (net return -0.31%, CAGR -0.04%, Sharpe -0.15, maximum drawdown -43.1%). Per-order sensitivity model (0.0035 USD per share, 0.35 USD minimum, 3 basis points of slippage):

| equity (USD) | net USD (return) | cost USD | cost % equity | CAGR | net Sharpe | max DD |
|---|---|---|---|---|---|---|
| 5,000 | -397 (-7.9%) | 421 | 8.4% | -1.14% | -0.21 | -43.5% |
| 10,000 | -494 (-4.9%) | 580 | 5.8% | -0.70% | -0.19 | -43.3% |
| 25,000 | -800 (-3.2%) | 1,073 | 4.3% | -0.45% | -0.18 | -43.3% |
| 50,000 | -1,350 (-2.7%) | 1,928 | 3.9% | -0.38% | -0.17 | -43.2% |
| 100,000 | -2,516 (-2.5%) | 3,697 | 3.7% | -0.35% | -0.17 | -43.2% |
| 250,000 | -6,130 (-2.5%) | 9,105 | 3.6% | -0.34% | -0.17 | -43.2% |

The per-order minimum matters a little for small accounts; the verdict does not change with capital. Cost sweep (basis points): CAGR +0.23% at 0, -0.04% at 3, -0.67% at 10, -2.0% at 25; zero cost is still far below both benchmarks.

## Lesson
Compare against the benchmark that takes the same risk and against a random version of your own selection rule before reading any single equity curve, and remember that a test on today's index members is a test on survivors.

## What I would do differently
- State the benchmark and the placebo before running anything.
- Use point-in-time data that includes delisted names, or say loudly that it is not.
- Pre-register the lookback and show its neighbours.

## Implementation notes
The published code does the following. It is a starting point: change the lookback, the number of names or the filters and re-run the test.
1. **Momentum lookback.** 105 days (five months of 21 trading days), with a 21-day skip. The ten-pair sensitivity in section 9.3 shows the conclusion does not depend on it.
2. **Scope.** The default path is HRP with a volatility target. Index-trend filters, a VIX filter, meta-labelling and Kelly sizing are not included.
3. **Data.** The notebook reads the price and membership tables from `AUTOPSY_DATA_DIR`. There is no network access and no downloader.
4. **Capital.** 100,000 USD for illustration, with a capital sweep and a per-order cost sensitivity.
5. **Early rebalances.** Leading rebalances with too few rankable names are skipped, and remaining fallbacks use a sorted order, so results are deterministic.
6. **Tests.** Survivorship measurement, alpha regression, paired Sharpe bootstrap, random-selection placebo, lookback sensitivity, capital and cost sweeps, and plots are part of the notebook. PDF and CSV writers and a command-line entry point are not included.

## Reproduce
1. `pip install -e ../..` and the `notebooks` extra (pyarrow, matplotlib).
2. Put the two files in a folder and `export AUTOPSY_DATA_DIR=<folder>` (names and columns in `data_schema.md`).
3. `jupyter nbconvert --to notebook --execute notebook.ipynb` (about 4 minutes, mostly the 100 placebo runs).
4. Synthetic mode: `AUTOPSY_SYNTHETIC=1 jupyter nbconvert --to notebook --execute notebook.ipynb`.

## Caveats
Survivorship bias (see the warning above) makes the strategy look better than a point-in-time version would. Fractional shares are assumed. The cash rate is a constant 4.5%. Educational material, not financial advice.
