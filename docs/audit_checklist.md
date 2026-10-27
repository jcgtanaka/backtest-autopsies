# Audit checklist (edge leak and licensing)

Run for every script and every notebook before it enters the repo. Work on a
copy and never edit the source file. Keep the dated log outside the repo.

| Done | Check | Where to look |
|------|-------|---------------|
| [ ] | Parameter values are stated in the case as the starting point of that case (lookbacks, thresholds, weights). | Constants, dict literals, argparse defaults |
| [ ] | Leverage multipliers and position sizing rules are stated or absent, never implied. | Names like lev, mult, size, kelly |
| [ ] | Every swept grid is described in the case text. | Grid definitions, itertools.product, config dicts |
| [ ] | Stop-loss or take-profit values, if any, are stated in the case. | Names like sl, tp, stop, target |
| [ ] | Gate thresholds, if any, are stated in the case. | Gate or filter conditions on vol spread |
| [ ] | Selected parameter sets are labelled as the values this case tests. | compute_pbo style code |
| [ ] | Capital is a single constant (100,000 USD for illustration) with a capital sweep. | Capital constants |
| [ ] | No local paths, usernames, account IDs, API keys, hostnames. | Strings starting with a slash or a drive letter, os.environ |
| [ ] | Comments reviewed, and the executable code read as well; comments can be out of date. | All comments and docstrings |
| [ ] | Notebook outputs reviewed cell by cell: no raw rows and no vendor data values. | Every output cell, figure titles, legends |
| [ ] | Git history clean: fresh init, no file ever contained a secret. | git log -p, secret scanner |
| [ ] | Counts such as grid sizes are stated consistently in README and notebook. | README, notebook text |
| [ ] | Every parameter set, universe and rule the case runs is listed in the case README under "Implementation notes". | Parameters, universes, candidate sets |
| [ ] | Reproducibility checked: the published code reproduces the numbers in the README. | Re-run |
| [ ] | Mechanical scan run and logged with the date (paths, usernames, keys, em dashes, head and tail calls). | Audit log |
| [ ] | `python tools/publish_gate.py` passes. | Repo root |
| [ ] | Vendor terms status written down; no input row count, date range, cardinality or fingerprint output remains. | `DATA_LICENSING.md` |
