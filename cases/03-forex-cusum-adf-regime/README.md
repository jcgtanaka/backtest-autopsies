# Backtest Autopsy #3: a CUSUM and rolling-ADF regime router for six FX pairs, starved of regime events

Tags: [regime starvation](../../docs/taxonomy.md#regime-starvation) (main), [cost model](../../docs/taxonomy.md#cost-model) (secondary)

**Verdict:** the mean-reversion branch, the only new part of the router, produced **17 development trades** in 11 independent episodes. The mean-reversion regime exists on 7 to 35 days per pair (0.3% to 1.3% of days) in episodes of 1 to 16 days. With 17 trades and a one-bar trade dispersion of about 47 basis points, the smallest edge the sample could detect is about 32 basis points per trade; a 5 basis point edge would need about 705 trades. The blended record is the trend branch, which is the plain moving-average baseline: on 100,000 USD of illustrative equity the baseline returns -37.9% net over the development window and the routed strategy -27.4% (annualised Sharpe -1.16 and -0.97), against +7.4% and +6.6% mid-to-mid before the bid/ask spread and commission.

Outputs below come from a run on real data (not redistributed). The synthetic mode (`AUTOPSY_SYNTHETIC=1`) runs the pipeline end to end on a synthetic quote panel and will NOT reproduce the failure.

**Initial equity.** The initial equity of 100,000 USD is an illustrative assumption; see the capital sweep (section 11 of the notebook) for 5,000 to 250,000 USD. The values below are the starting point for this case. Change them and re-run the test to see whether the verdict holds.

## Hypothesis
FX pairs alternate between trending and mean-reverting regimes. A causal CUSUM detector should identify the trending ones (trade the moving-average direction) and a rolling ADF test on the residual of a pair against a related pair should identify the mean-reverting ones (fade the residual). Routing each day to the right behaviour, and staying flat when the two detectors disagree, should beat an always-on moving-average rule.

## Data
Minute-level bid and ask closes for six USD FX pairs from a broker data export, collapsed to one daily bid/ask close per pair. Key `(date, asset)`. See `data_schema.md`. No vendor rows are published; the notebook prints schema checks only (no counts, dates or hashes of the input).

## Method
Causal CUSUM on standardised log returns (prior-window standardisation, cooldown, five-day persistence) for the trend flag; rolling 120-day regression of each pair on a fixed related pair and an ADF test on the residual with a Bonferroni-adjusted level, a half-life bound and a five-day streak for the mean-reversion flag. Four signals (baseline moving average, CUSUM gate, ADF gate, combined routing) traded as one-bar round trips at executable bid/ask prices plus a flat commission add-on; the 2025+ window is retrospective and reported separately. Full metrics table and twelve plots in the notebook.

## Result
Development window, net: baseline -37.9% (maximum drawdown -41.2%, 13,116 pair-day trades), combined routing -27.4% (maximum drawdown -30.9%, 9,207 trades). Mid-to-mid (before spread and commission) the two are +7.4% and +6.6%. The 95% interval of the mean daily return is [-3.4, -0.9] basis points for the baseline and [-2.4, -0.4] for the routing. Retrospective window: -21.1% and -12.7%.

## Killing test
Count the independent events behind the conditional claim (notebook section 10). Funnel: the Bonferroni-adjusted ADF level is passed on 704 development pair-days; after the half-life bounds, the five-day streak, the trend veto and the entry threshold, 17 trades remain. Episode-level (cluster) bootstrap 95% interval of the mean mean-reversion trade return: [-16, +15] basis points. Relaxing the per-test level (diagnostic only, nothing is chosen as the headline): 93 trades at 0.05, 148 at 0.10, 216 at 0.20, with the mean trade return still negative (-5.4, -2.7 and -0.6 basis points) and every interval containing zero. The decision rule declared in the notebook before the test returns "retire or change the hypothesis" (fewer than two regimes with 30 or more trades; positive expectancy in fewer than 60% of pairs and of calendar years).

## Capital sweep (section 11 of the notebook)
Only the initial equity changes (same signals, detectors, costs and windows; nothing retuned). The strategy sizes each pair at one sixth of equity and its costs are proportional (spread and a basis-point commission), so no per-order minimum applies.

| equity (USD) | gross USD (mid-to-mid) | cost USD | cost % equity | net USD (return) | net Sharpe | max DD |
|---|---|---|---|---|---|---|
| 5,000 | 329 | 1,699 | 34.0% | -1,370 (-27.4%) | -0.97 | -30.9% |
| 10,000 | 658 | 3,398 | 34.0% | -2,740 (-27.4%) | -0.97 | -30.9% |
| 25,000 | 1,645 | 8,495 | 34.0% | -6,850 (-27.4%) | -0.97 | -30.9% |
| 50,000 | 3,290 | 16,990 | 34.0% | -13,701 (-27.4%) | -0.97 | -30.9% |
| 100,000 | 6,579 | 33,981 | 34.0% | -27,401 (-27.4%) | -0.97 | -30.9% |
| 250,000 | 16,448 | 84,951 | 34.0% | -68,503 (-27.4%) | -0.97 | -30.9% |

What scales: the USD amounts. What does not: every ratio, because nothing is a fixed per-order fee. The verdict does not change with capital. Commission sensitivity (spread unchanged): the baseline's development return is -22.8% with no commission add-on and -67.8% with four times the add-on; the sign never changes.

## Lesson
Count the independent events behind each branch of a router before reading the blended P&L: if a regime has a few dozen trades in a handful of episodes, no test was possible, and the right conclusion is "nothing to estimate", not "does not work".

## What I would do differently
- Compute the funnel and the minimum detectable edge first, before any P&L.
- Pick the regime definition for event count (looser, pre-registered, more instruments or intraday bars), not for purity.
- Test the trend branch against a volatility-matched baseline separately from the router.

## Implementation notes
The published code does the following. It is a starting point: change the parameters and re-run the test.
1. **Moving-average pair.** The trend flag uses the pair 9 / 37. The number of mean-reversion regime days and trades depends on this pair (17 trades here). The conclusion does not depend on it.
2. **Loader.** The minute-level reading (chunked read of the timestamp and the bid/ask closes, sort, last row of duplicated timestamps) and the daily collapse (last valid bid and ask of each calendar day) are written out in the notebook. Unused columns (open, high, low) are not read.
3. **Data.** The raw file is read from `AUTOPSY_DATA_DIR` (name in `data_schema.md`). No absolute paths are used; there is no network access.
4. **Capital.** The strategy is return-based. USD figures use 100,000 USD for illustration, with a capital sweep from 5,000 to 250,000 USD and a commission sweep.
5. **Bootstrap.** Fixed seeds and 2,000 resamples, so results are repeatable.
6. **Structure.** The regime logic is split into a detector step and a classification step (so the sensitivity table does not repeat the ADF), the trade loop is vectorised, and a mid-to-mid return is recorded next to the executable return. The funnel, power table, episode bootstrap, sensitivity table, capital sweep, commission sweep and plots are part of the notebook. PDF and CSV writers and a command-line entry point are not included.

## Reproduce
1. `pip install -e ../..` and the `notebooks` extra (statsmodels, pyarrow, matplotlib).
2. Put the minute-level FX file in a folder and `export AUTOPSY_DATA_DIR=<folder>` (name and columns in `data_schema.md`).
3. `jupyter nbconvert --to notebook --execute notebook.ipynb` (about half a minute after the first run, which also builds the daily cache from the minute file).
4. Synthetic mode: `AUTOPSY_SYNTHETIC=1 jupyter nbconvert --to notebook --execute notebook.ipynb`.

## Caveats
A signal at the close of day `t` is assumed executable at that same daily bid/ask close: a modelling simplification, not evidence of live fill quality. The 2025+ window is retrospective, not fresh out-of-sample evidence. The daily bid/ask close is the last quote of a calendar day in a fixed UTC-5 clock. Educational material, not financial advice.
