# Pre-backtest checklist

One line per lesson. Each line names the failure tag and, where a published
case taught it, links to that case. Lines marked "guide" are standard checks
that no published case has needed yet.

| | Check before you trust a backtest | Tag | Taught by |
|---|---|---|---|
| [ ] | Target: is the model trained and scored on the traded return, and does it beat a mechanical rule built from the same inputs? | proxy target | [case 1](../cases/01-forex-ml-sma-direction/) |
| [ ] | Gross first: does the signal show skill (hit rate, correlation, out-of-sample R-squared) before any sizing or portfolio machinery? | proxy target, cost model | [case 1](../cases/01-forex-ml-sma-direction/), [case 2](../cases/02-var-varma-daily-refit-cost-model/) |
| [ ] | Trial count: how many variants did you try, including discarded ones, and is it passed to PBO and the deflated Sharpe? | multiple testing | guide |
| [ ] | Selection step: did you measure the PBO of the selection rule itself (and read more than one PBO estimator)? | multiple testing | guide |
| [ ] | Holdout: is there an untouched holdout, touched once, and is it long enough to say anything? | multiple testing, regime starvation | guide |
| [ ] | Independent events: how many truly independent observations (not days or overlapping labels) support the claim? | regime starvation | [case 1](../cases/01-forex-ml-sma-direction/) |
| [ ] | Costs: what is the breakeven cost multiple and how does it compare with realistic costs? | cost model | [case 1](../cases/01-forex-ml-sma-direction/), [case 2](../cases/02-var-varma-daily-refit-cost-model/) |
| [ ] | Fixed per-order minimums versus proportional costs: do tickets, minimum commissions or lot sizes dominate at your capital? | cost model | [case 2](../cases/02-var-varma-daily-refit-cost-model/) |
| [ ] | Cost convention: is a round turn charged once per open-and-close, or twice? Is the convention stated and the result shown under both? | cost model | guide |
| [ ] | Capital sweep: does the verdict hold from 5,000 to 250,000 USD with nothing retuned, and do you know what scales and what does not? | cost model | [case 2](../cases/02-var-varma-daily-refit-cost-model/) |
| [ ] | Turnover: what is the implied turnover and cost drag before the P&L is read? | cost model | [case 2](../cases/02-var-varma-daily-refit-cost-model/) |
| [ ] | Reproducibility: does the published code reproduce the numbers reported in the README? | reproducibility | [case 2](../cases/02-var-varma-daily-refit-cost-model/) |
| [ ] | Units: is every return, rate and volatility in the same unit and period, and does the result pass a plausibility bound? | units bug | guide |
| [ ] | Overlapping windows: do labels or features overlap between train and test? Did you purge and embargo? | leakage | guide; applied in case [1](../cases/01-forex-ml-sma-direction/) |
| [ ] | Execution: does the result survive a one-bar delay on the signal? | execution | guide |
| [ ] | Frequency: is periods per year correct for this data (no hard-coded 252)? | units bug | guide |
| [ ] | Seeds: are all random draws seeded and logged? | reproducibility | guide |
| [ ] | Data vintage: could any value have been revised or unavailable at decision time? | leakage | guide |
| [ ] | Noise benchmark: is the headline believable relative to a pure-noise series run through the same pipeline? | all | guide |
