# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Case 1: random forest on future SMA direction (proxy target, cost model).
- Case 2: daily-refit VAR on 19 assets, no forecast skill, then costs
  (cost model).
- Case 3: CUSUM and rolling-ADF FX regime router (regime starvation, cost
  model).
- Case 4: free-data FX factor strategy with a weekly sensitivity variant (no
  signal, cost model).
- Case 5: S&P 500 momentum and HRP against SPY and vol-targeted SPY (no edge vs
  benchmark; survivorship warning).
- Case 6: equal-weight crypto basket, minimum ticket and ruin check (cost model,
  no ruin floor).
- `autopsy_common`: `regimes` (run lengths), `ruin` (ruin report and floor) and
  new metrics (bootstrap mean and correlation intervals, cross-sectional rank
  IC, alpha-beta regression), with tests.
- Taxonomy: `no edge vs benchmark` and `no ruin floor`; `no signal` added to the
  table.
- `autopsy_common` package: metrics, performance report, plots, walk-forward,
  capital sweep, synthetic data helpers and schema checks, with tests.
- Docs: taxonomy, case template, pre-backtest checklist, audit checklist.
- `DATA_LICENSING.md` and MIT `LICENSE`.
- `tools/publish_gate.py`, a check-only gate for raw-data-looking content,
  paths, secrets, em dashes, data files and `.gitignore` patterns.
- CI workflow (lint, types, tests, gate, synthetic notebook execution) and
  pre-commit configuration.
