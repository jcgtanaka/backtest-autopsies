# Backtest Autopsy #4: a free-data FX factor strategy (spot factors, CFTC positioning, policy rates), no signal

Tags: [no signal](../../docs/taxonomy.md#no-signal) (main), [cost model](../../docs/taxonomy.md#cost-model) (secondary)

**Verdict:** over the development window, on 100,000 USD of illustrative equity, the headline strategy (spot factor + CFTC positioning + policy rates, a capped currency-neutral book of six USD pairs at executable bid/ask prices) returns -10.9% net: CAGR -1.63%, annualised Sharpe -0.65, maximum drawdown -13.6%. There is no gross edge to begin with: gross return -4.7% (gross Sharpe -0.27, 90% interval [-0.76, +0.29]), mean daily rank IC +0.013 (t = 1.32), directional hit rate 50.2% (95% interval 49.4% to 51.1%), and 87% of day-shuffled copies of the held weights earn at least as much gross P&L as the actual book (permutation p = 0.87). The spread and the commission then take a further 6.7% of equity. A weekly, low-turnover variant loses less (-6.1% net, -5.6% gross) and does not turn the sign.

Outputs below come from a run on real data (not redistributed). The synthetic mode (`AUTOPSY_SYNTHETIC=1`) runs the pipeline end to end on synthetic quotes, positioning and rates and will NOT reproduce the failure.

**Initial equity.** The initial equity of 100,000 USD is an illustrative assumption; see the capital sweep (section 11 of the notebook) for 5,000 to 250,000 USD. The values below are the starting point for this case. Change them and re-run the test to see whether the verdict holds.

## Hypothesis
Free, published inputs carry next-day information about currencies: a cross-sectional blend of spot momentum, reversal and breakout, CFTC leveraged-money positioning and policy-rate levels, held as a capped, currency-neutral long-short book, should earn a positive gross return that survives executable costs.

## Data
Three inputs: minute-level bid and ask closes for six USD pairs from a broker data export (collapsed to a daily bid/ask close), the public CFTC *Traders in Financial Futures* annual archives, and the public BIS central bank policy-rate bulk file. Keys `(date, asset)`, `(currency, report_date)` and `(currency, observation_date)`. See `data_schema.md`. No vendor rows are published; the notebook prints schema checks only (no counts, dates or hashes of the input).

## Method
Currency-level features from the pair relationships (robust cross-sectional z-scores of momentum, reversal and breakout; strictly prior policy rate; CFTC net positioning z-score joined four business days after the Tuesday report), a fixed score blend (0.60 spot, 0.30 positioning, 0.10 rate), a volatility-scaled, mean-neutral, capped (25% per currency, 80% gross) book translated into six pair weights, one-day-delayed holding, quoted half-spread plus a 0.5 basis point commission add-on. A walk-forward ridge-logistic overlay is the secondary layer. The 2025+ window is retrospective and reported separately. A weekly variant (Friday anchor, persistence gate, turnover buffer, next-close execution) is a sensitivity block in the same notebook. Full metrics table and fifteen plots in the notebook.

## Result
Development window, net: spot factor only -10.8% (Sharpe -0.65), positioning only -5.1% (Sharpe -0.33), spot + positioning + rates -10.9% (Sharpe -0.65), overlay -4.3% (Sharpe -0.58; active on about 11% of days). Gross returns are -3.9%, -3.1%, -4.7% and -2.4%. Retrospective window for the headline: -2.3%.

## Killing test
Four checks that need no cost model (notebook section 10). Rank IC of the headline score against the next day's currency return: mean 0.013, t = 1.32 (days treated as independent, which flatters the signal). Hit rate 50.2% with a 95% interval that contains 50%. Permutation of the day order of the held weights against realised pair returns (2,000 shuffles): the actual gross sum sits in the body of the shuffled distribution (p = 0.87 for the headline, 0.85, 0.79 and 0.92 for the other three). Block-bootstrap interval of the gross Sharpe contains zero. The decision rule's hurdles fail on the CAGR band and on the stability of years (2 of 7 positive) and pairs (2 of 6 contribute positively before costs) and on the absence of a fresh holdout.

## Capital sweep (section 11 of the notebook)
Only the initial equity changes (same signals, caps, windows and costs; nothing retuned). The book holds weights as fractions of equity and its costs are proportional (half-spread and a basis-point commission), so no per-order minimum applies.

| equity (USD) | gross USD | cost USD | cost % equity | net USD (return) | net Sharpe | max DD |
|---|---|---|---|---|---|---|
| 5,000 | -235 | 307 | 6.1% | -543 (-10.9%) | -0.65 | -13.6% |
| 10,000 | -471 | 614 | 6.1% | -1,085 (-10.9%) | -0.65 | -13.6% |
| 25,000 | -1,177 | 1,536 | 6.1% | -2,713 (-10.9%) | -0.65 | -13.6% |
| 50,000 | -2,354 | 3,071 | 6.1% | -5,425 (-10.9%) | -0.65 | -13.6% |
| 100,000 | -4,708 | 6,142 | 6.1% | -10,850 (-10.9%) | -0.65 | -13.6% |
| 250,000 | -11,769 | 15,356 | 6.1% | -27,125 (-10.9%) | -0.65 | -13.6% |

What scales: the USD amounts. What does not: every ratio, because nothing is a fixed per-order fee. Cost multiplier sweep (portfolio re-run, development window): -4.7% at zero cost, -7.8% at half the modelled cost, -10.9% at the modelled cost, -16.6% at twice. There is no multiplier at which it is profitable, because gross is negative. The verdict does not change with capital.

## Weekly variant (notebook section 12)
Friday anchor, next-close execution, a currency may change sign only after two consecutive weekly anchors, rebalance only when a weight moves at least five points. Turnover falls by 85% (sum of absolute weight changes 80 versus 524); the headline weekly strategy returns -6.1% net (CAGR -0.90%, Sharpe -0.32) and -5.6% gross, with a gross Sharpe interval of [-0.80, +0.20]. It loses less because it pays less cost on a signal that earns nothing; its gross return is not better than the daily one.

## Lesson
A factor is not a signal until its information survives a test that needs no cost model: compute the rank IC, the hit-rate interval and a day-shuffle permutation of the held weights before building the portfolio.

## What I would do differently
- Run the information tests first; they need a score matrix and next-day returns, nothing else.
- Choose the rebalance horizon from the signal (positioning and policy rates are slow); the weekly variant should have been the first test.
- Pool more currencies and more history before reading year-by-year stability, and keep a genuinely untouched holdout.

## Implementation notes
The published code does the following. It is a starting point: change the factors, caps or blend and re-run the test.
1. **Factors.** All spot factors, the positioning and rate inputs, the caps, the no-trade states and the overlay are included. A weekly variant is included as a sensitivity block (it is not a separate case).
2. **Data.** The public CFTC and BIS inputs and the wide minute file are read from `AUTOPSY_DATA_DIR`. Nothing is downloaded by the notebook, and no absolute paths are used.
3. **Quotes and rates.** The notebook reads the wide minute file that the other FX cases use, keeps quotes with bid above zero and ask not below bid, takes the last valid quote of each calendar day, and builds daily policy rates directly from the BIS bulk file (daily series of the seven economies).
4. **Capital.** The strategy is return-based. USD figures use 100,000 USD for illustration, with a capital sweep from 5,000 to 250,000 USD and a cost multiplier sweep.
5. **Implementation.** The robust z-score is computed with group transforms instead of a per-date loop; gross, spread and commission returns are recorded separately. PDF and CSV writers and command-line entry points are not included.
6. **Tests.** The rank IC, hit-rate interval, day-shuffle permutation test, gross Sharpe bootstrap, cost multiplier sweep, capital sweep and plots are part of the notebook. Bootstraps and the permutation test use fixed seeds.

## Reproduce
1. `pip install -e ../..` and the `notebooks` extra (pyarrow, matplotlib).
2. Put the three inputs in a folder and `export AUTOPSY_DATA_DIR=<folder>` (names in `data_schema.md`).
3. `jupyter nbconvert --to notebook --execute notebook.ipynb` (about one minute after the first run, which also builds the daily cache from the minute file).
4. Synthetic mode: `AUTOPSY_SYNTHETIC=1 jupyter nbconvert --to notebook --execute notebook.ipynb`.

## Caveats
Weights set at the close of day `t` are held over `t+1` at that day's mid with the half-spread charged on the traded amount, a modelling simplification, not evidence of live fill quality. Policy rates are a proxy, not tradable carry; USD positioning comes from the dollar index future, which differs from the currency futures used for the other six. The CFTC publishes no historical release timestamps; the four-business-day availability lag is an assumption. The 2025+ window is retrospective, not fresh out-of-sample evidence. Educational material, not financial advice.
