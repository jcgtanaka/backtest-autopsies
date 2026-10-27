# Backtest Autopsy #6: an equal-weight crypto basket with a minimum ticket

Tags: [cost model](../../docs/taxonomy.md#cost-model)

**Verdict:** an equal-weight basket of five crypto assets, rebalanced to equal weight, loses money on 100,000 USD of illustrative equity: daily rebalancing ends at 63,551 USD (-36.4%, maximum drawdown -80.0%) against 86,148 USD before costs, monthly rebalancing at 85,803 USD (-14.2%) against 88,567 USD before costs. The basket lost gross, so most of the loss is the market; costs add 18,220 USD (daily) or 2,643 USD (monthly). **The ruin does not survive the capital sweep at the headline size:** equity goes below zero only for daily rebalancing at 10,000 USD or less (2 of 24 runs from 5,000 USD up; none of weekly, biweekly or monthly), never at 25,000 USD or more, and at an illustrative 1,000 USD tiny account for three of four frequencies. The mechanism is a 1.75 USD minimum commission per order: orders below about 972 USD of notional pay the minimum, so on a small account the fixed fee is 97% of the cost of daily rebalancing (53% at 100,000 USD).

Outputs below come from a run on real data (not redistributed). The synthetic mode (`AUTOPSY_SYNTHETIC=1`) runs the pipeline end to end on synthetic prices and will NOT reproduce the failure.

**The strategy depends on its initial equity.** The fixed 1.75 USD minimum commission dominates small accounts, so the same rules lose more or less depending on the starting capital. The ruin result above is a property of small accounts, not of the headline size.

**Initial equity.** The initial equity of 100,000 USD is an illustrative assumption; see the capital sweep (sections 7 and 8 of the notebook) for 5,000 to 250,000 USD, plus an extra illustrative 1,000 USD tiny account in the ruin table.

## Hypothesis
Nothing to predict: a "basic" equal-weight, periodically rebalanced portfolio of five crypto assets, tested on how its rebalance frequency interacts with costs.

## Data
One-minute trades for five coins from a broker data export, collapsed to a daily close, high and low per coin. Key `(date, asset)`. See `data_schema.md`. No vendor rows are published; the notebook prints schema checks only.

## Method
Equal weight over the assets listed at each date; daily, weekly, biweekly or monthly rebalancing with buy-and-hold drift between; every order pays max(18 basis points of notional, 1.75 USD) plus slippage of 5% of the day's high-low range times notional; no ruin floor (equity can go negative); annualised on 365 days. The ruin sweep and the ruin-floor variant (equity frozen at zero from the first breach) are new. Full metrics table and eleven plots in the notebook.

## Result
Headline (100,000 USD): daily final 63,551 USD (-36.4%, Sharpe 0.19), weekly 82,444 USD (-17.6%), biweekly 84,230 USD (-15.8%), monthly 85,803 USD (-14.2%, Sharpe 0.29). The Sharpe is positive while the total return is negative because the volatility is about 68% a year and volatility drag turns a positive arithmetic mean into a negative compounded return.

## Killing test
The capital sweep with a ruin check (section 7), four frequencies by seven equity levels. Equity at or below zero on some day: daily at 1,000, 5,000 and 10,000 USD (first breach after about 137, 376 and 661 days); weekly and biweekly at 1,000 USD only; monthly never. Lowest equity reached by daily rebalancing: -23.7 USD at 5,000, -17.6 at 10,000, 3,425 at 25,000. Share of cost that is the fixed minimum (daily): 97% at 5,000 USD, 90% at 25,000, 75% at 50,000, 53% at 100,000, 24% at 250,000.

## Capital sweep (sections 7 and 8 of the notebook)
Only the initial equity changes (nothing retuned). Daily rebalancing:

| equity (USD) | gross USD | cost USD | cost % equity | net return | net Sharpe | fixed part of cost USD | lowest equity USD |
|---|---|---|---|---|---|---|---|
| 5,000 | -693 | 2,700 | 54.0% | -100.3% | -1.36 | 2,612 | -24 |
| 10,000 | -1,385 | 4,792 | 47.9% | -100.1% | -1.59 | 4,574 | -18 |
| 25,000 | -3,463 | 13,068 | 52.3% | -82.2% | -0.24 | 11,712 | 3,425 |
| 50,000 | -6,926 | 14,752 | 29.5% | -51.6% | 0.10 | 11,019 | 12,240 |
| 100,000 | -13,852 | 18,220 | 18.2% | -36.4% | 0.19 | 9,739 | 25,911 |
| 250,000 | -34,631 | 29,636 | 11.9% | -27.7% | 0.23 | 6,960 | 66,156 |

Monthly rebalancing:

| equity (USD) | gross USD | cost USD | cost % equity | net return | net Sharpe |
|---|---|---|---|---|---|
| 5,000 | -572 | 554 | 11.1% | -25.4% | 0.25 |
| 10,000 | -1,143 | 648 | 6.5% | -19.4% | 0.27 |
| 25,000 | -2,858 | 944 | 3.8% | -15.8% | 0.29 |
| 50,000 | -5,717 | 1,478 | 3.0% | -14.7% | 0.29 |
| 100,000 | -11,433 | 2,643 | 2.6% | -14.2% | 0.29 |
| 250,000 | -28,584 | 6,335 | 2.5% | -14.0% | 0.29 |

What scales: notional per order and the proportional costs. What does not: the 1.75 USD minimum, which is why the cost share of equity rises faster than 1 over equity as the account shrinks. The verdict (cost model) holds at every level; the ruin appears only at small equity and high frequency.

## Lesson
Put the fee floor and a ruin floor in the model before reading the P&L, and run the capital sweep before claiming a ruin: the dramatic result (an account below zero) is a small-account, high-frequency result, and stating it at the headline size would have been wrong.

## What I would do differently
- Run the ruin sweep first and choose the headline after it.
- Model the fixed part of fees separately and print the break-even ticket next to the first result.
- Rebalance on a drift band, not on a clock, and stop the simulation at the margin call.

## Implementation notes
The published code does the following. It is a starting point: change the assets, frequencies or cost schedule and re-run the test.
1. **Capital.** 100,000 USD for illustration, with a 5,000 to 250,000 USD sweep (plus an extra 1,000 USD tiny account in the ruin table).
2. **Costs.** 18 basis points with a 1.75 USD minimum per order follow the broker's published crypto commission schedule (not re-verified against the broker's current page for this publication). The slippage of 5% of the day's range is an assumption. Both are named as such in the notebook.
3. **Helpers.** The cost function and the data loader are written out in the notebook; the loader reads the daily panel from `AUTOPSY_DATA_DIR`.
4. **Reporting.** Fixed-versus-proportional cost split, order counts, ruin report and ruin-floor variant, capital and ruin sweeps and plots are part of the notebook. There is no benchmark (the baseline is the same portfolio without costs). PDF and CSV writers and a command-line entry point are not included.

## Reproduce
1. `pip install -e ../..` and the `notebooks` extra (pyarrow, matplotlib).
2. Put the minute-level crypto file in a folder and `export AUTOPSY_DATA_DIR=<folder>` (name and columns in `data_schema.md`).
3. `jupyter nbconvert --to notebook --execute notebook.ipynb` (about 45 seconds; the first run also builds a daily cache).
4. Synthetic mode: `AUTOPSY_SYNTHETIC=1 jupyter nbconvert --to notebook --execute notebook.ipynb`.

## Caveats
The minimum commission and the 18 basis points were not re-verified against the broker's current page. Slippage is an assumption, not a fill. The simulation lets equity go below zero and keeps trading, which no account can do; the ruin-floor variant shows the stopped path. Crypto assets can lose all of their value. Educational material, not financial advice.
