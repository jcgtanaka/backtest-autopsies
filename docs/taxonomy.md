# Failure taxonomy

Nine tags. Every case gets one primary tag and optionally one secondary tag.
The tag appears in the README table and as a post hashtag. A tag is only used
when the case reports its quantified verdict.

| Tag | Definition | Typical killing test | Quantified verdict | Cases |
|-----|------------|----------------------|--------------------|-------|
| [leakage](#leakage) | Information from the future or from the test set reached the training or signal step. | Purged and embargoed CV; shifted-label check; shuffle test. | Score drop after purge (for example Sharpe before and after). | none yet |
| [multiple testing](#multiple-testing) | Many variants were tried and the best was reported without adjusting. | PBO via CSCV; deflated Sharpe with the true trial count. | PBO value; deflated Sharpe probability. none published yet (held for the next release) |
| [regime starvation](#regime-starvation) | Too few independent regime events to estimate anything. | Count independent events; bootstrap by event; CI width. | Number of independent events; CI width. | [3](../cases/03-forex-cusum-adf-regime/) |
| [units bug](#units-bug) | A scaling or unit error (daily vs annual, percent vs fraction) produced an implausible result. | Plausibility bounds; unit tests on known series. | Result before and after the fix. | none yet |
| [cost model](#cost-model) | Edge disappears after realistic spread, fees, slippage or financing. | Cost sweep; breakeven cost multiple. | Breakeven cost versus realistic cost. | [1](../cases/01-forex-ml-sma-direction/) (secondary), [2](../cases/02-var-varma-daily-refit-cost-model/), [3](../cases/03-forex-cusum-adf-regime/) (secondary), [4](../cases/04-forex-free-factor/) (secondary), [6](../cases/06-crypto-equal-weight-minimum-ticket/) |
| [execution](#execution) | The assumed fill was not obtainable (look-ahead on the close, stale quotes, liquidity). | Lag-the-signal test; fill-at-next-bar test. | Return with one-bar delay. | none yet |
| [proxy target](#proxy-target) | The model predicts a label that does not map to tradable return. | Score the traded return, not the label; compare with a mechanical baseline built from the same inputs. | Label accuracy lift versus signal-to-return correlation and gross Sharpe with its interval. | [1](../cases/01-forex-ml-sma-direction/) |
| [no signal](#no-signal) | The forecast is indistinguishable from chance, so there is no gross edge. | Hit rate and out-of-sample R-squared against a zero forecast; label permutation; rank IC. | Hit rate with its interval; permutation p-value. | [2](../cases/02-var-varma-daily-refit-cost-model/), [4](../cases/04-forex-free-factor/) |
| [no edge vs benchmark](#no-edge-vs-benchmark) | A reasonable-looking equity curve does not beat the benchmark that takes the same risk, nor a random version of its own selection. | Alpha regression on the benchmark and on a volatility-matched benchmark; placebo with random selection. | Alpha with its t-statistic; percentile of the strategy among placebo runs. | [5](../cases/05-sp500-top5-hrp/) |
| [no ruin floor](#no-ruin-floor) | The simulation lets equity go to zero or below and keeps trading, or ignores a fixed fee floor that dominates small accounts. | Capital sweep with a ruin check; stop the path at the first breach; split the fixed part of the cost. | Smallest equity and highest frequency at which equity reaches zero; fixed share of the cost. | [6](../cases/06-crypto-equal-weight-minimum-ticket/) (secondary) |

## leakage

Definition: information from the future or from the test set reached training
or signal construction. Killing test: purged and embargoed CV, shifted-label
check, shuffle test. Verdict: score before and after the purge. No case has it
as the primary failure yet; case 1 applies purge and embargo as a
precaution.

## multiple testing

Definition: many variants were tried and the best one was reported as if it
were the only one. Killing test: PBO by CSCV with the whole trial matrix,
deflated Sharpe with the true trial count. Verdict: PBO value and deflated
Sharpe probability. No published case uses it yet; it is held for the next
release.

## regime starvation

Definition: too few independent regime events support the claim, so any
estimate is noise. Killing test: count independent events, bootstrap by event,
report the interval width. Verdict: number of independent events and interval
width. Case 3 uses it as the main tag (17 mean-reversion trades in 11 independent episodes, minimum detectable edge about 32 basis points per trade).

## units bug

Definition: a scale or unit error such as daily versus annual or percent
versus fraction. Killing test: plausibility bounds, unit tests on a known
series. Verdict: the result before and after the fix. No case yet.

## cost model

Definition: gross edge disappears after realistic spread, commission,
slippage or financing. Killing test: cost sweep and breakeven multiple.
Verdict: breakeven versus realistic cost. Cases 1 and 2 each report a cost
sweep; case 2 adds a capital sweep. Case 6 is
the main case for a per-order minimum fee (daily rebalancing: -36.4% against
-14.2% for monthly, 18.2% of equity in costs against 2.6%).

## execution

Definition: the assumed fill could not be obtained (close look-ahead, stale
quote, liquidity). Killing test: lag the signal one bar, fill at the next bar.
Verdict: return with a one-bar delay. No case yet.

## proxy target

Definition: the model is trained and scored on a label that does not map to
tradable return, so a better label score does not imply a better P&L. Killing
test: score the traded outcome (signal versus next-period return, bootstrap
of the gross Sharpe) and compare with a mechanical rule that uses only past
prices. Verdict: the accuracy lift versus the gross Sharpe and its interval.
Case 1: accuracy 68.4% against a 61.8% baseline, gross Sharpe +0.07.

## no signal

Definition: the model's forecast is indistinguishable from chance, so the
traded return has no edge before costs. Killing test: hit rate and
out-of-sample R-squared against a zero forecast, a label-permutation test, and
a rank information coefficient. Verdict: hit rate with its confidence interval,
and the permutation p-value. Case 2: hit rate 51.2% (CI 49.2% to 53.3%),
permutation p 0.48, out-of-sample R-squared -0.049.

Also used by case 4: mean rank IC 0.013 (t = 1.32), hit rate
50.2% (interval 49.4% to 51.1%), day-shuffle permutation p = 0.87.

## no edge vs benchmark

Definition: the strategy's equity curve looks acceptable on its own but does
not beat the benchmark that takes the same risk (a volatility-targeted index
when the strategy targets volatility) and is not better than the same engine
with a random selection. Killing test: alpha regression on the index and on
the volatility-matched index with its t-statistic, a paired block bootstrap of
the Sharpe difference, and a placebo that draws the selection at random.
Verdict: alpha and its t-statistic; percentile of the strategy Sharpe among the
placebo runs. Case 5: CAGR -0.04% against 14.2% for SPY and 11.0% for the
volatility-targeted SPY, alpha -8.4% (t = -1.65) against the volatility-targeted
SPY, Sharpe at the 9th percentile of 100 random-selection runs. Every
stock-based case of this kind carries a survivorship warning.

## no ruin floor

Definition: the simulation lets equity reach zero or below and keeps trading,
and/or a fixed per-order fee floor that is negligible at one size dominates at
another, so a result that is a loss at the headline size is ruin at a smaller
one. Killing test: run the capital sweep with a ruin check (does equity reach
zero, and when), stop the path at the first breach, and split the cost into its
fixed and proportional parts. Verdict: the smallest equity and the highest
frequency at which equity reaches zero, and the fixed share of the cost. The tag
is conditional: it is only used when the sweep shows the ruin, and it is
reported as small-account when the headline size survives. Case 6 (secondary):
equity reaches zero only for daily rebalancing at 10,000 USD or less (and at an
illustrative 1,000 USD for three of four frequencies); at 100,000 USD none of
the four frequencies does; the fixed minimum is 97% of the cost at 5,000 USD
and 53% at 100,000 USD.
