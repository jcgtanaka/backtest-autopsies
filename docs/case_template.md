# Case template

Copy this file into `cases/NN-<slug>/README.md`, then build `notebook.ipynb`
and `data_schema.md` next to it. A case is not done until every section has
content and the verdict contains a number.

## Folder contents

```
cases/NN-<slug>/
  README.md        story, verdict, how to get data
  notebook.ipynb   EXECUTED, outputs saved
  data_schema.md   column, dtype, meaning, units; key description
```

Anything used by two or more cases lives in `src/autopsy_common`.

## The seven sections

| Section | What to write |
|---------|---------------|
| Hypothesis | One or two sentences: what you believed would make money and why. |
| Data | Source recipe, frequency, key. Link `data_schema.md`. Describe structure only: no row counts, input date ranges or instrument counts. Never include vendor rows. |
| Method | How the strategy and the evaluation were built, including the validation scheme. State the parameter values the case tests. |
| Result | What the naive backtest showed, with the shared metrics. This is the "it looked good" part. |
| Killing test | The one test that killed it, why it is the right test, and the number. |
| Lesson | The transferable rule in one sentence, linked to a line of the pre-backtest checklist. |
| What I would do differently | Concrete process changes, three bullets, no apologies. |

## README skeleton

```
# Backtest Autopsy #N: <short title>

Tags: <primary-tag>[, <secondary-tag>]

**Verdict:** <one sentence with the number, with USD amounts on the stated illustrative equity>.

> **Scope.** One sentence on what is tested and that the verdict applies to the version tested; see "Implementation notes".

Outputs below come from a run on real data (not redistributed). The synthetic mode
(`AUTOPSY_SYNTHETIC=1`) runs the pipeline end to end on fake data and will NOT
reproduce the failure.

**Initial equity.** 100,000 USD is an illustrative assumption; see the capital
sweep section for 5,000 to 250,000 USD.

## Hypothesis
## Data
## Method
## Result
## Killing test
## Capital sweep
## Lesson
## What I would do differently
## Implementation notes
## Reproduce
## Caveats
```

Reproduce block:

1. `pip install -e ../..` and the `notebooks` extra.
2. Put the data files (schema in `data_schema.md`) in a folder and
   `export AUTOPSY_DATA_DIR=<folder>`.
3. `jupyter nbconvert --to notebook --execute notebook.ipynb` (state the time).
4. Synthetic mode: `AUTOPSY_SYNTHETIC=1 jupyter nbconvert --to notebook --execute notebook.ipynb`.

## Notebook structure (blog style)

The notebook reads as an article: short markdown, then the code and its
output, in this order.

1. Title, verdict, scope and implementation notes.
2. Settings cell: every parameter in one place, labelled as the value this case tests, and the
   initial equity as a single constant.
3. Data section (rules below).
4. Method and the naive backtest with the shared metrics table and plots.
5. The killing test, with its number in the text.
6. Capital sweep section (rules below).
7. Lesson and what to do differently.

## Data section rules

- Source and product described in words; no download of vendor data inside the
  published outputs.
- Schema table mirrored from `data_schema.md`, key and sort order stated.
- A schema check cell that fails early with a clear message.
- Print pass/fail schema checks only: no row counts, input date ranges,
  distinct counts, content fingerprints, `head()`, `tail()`,
  `describe()` of real data, no date-and-price rows, no asset names that
  identify a vendor product beyond what the README already states.
- A synthetic sample sized by the key levels, fixed seed, round values,
  labelled "synthetic, same schema as the real data".
- No cardinality summary or fingerprint of the input is published.

## Capital sweep rules

Every case runs the same pipeline at 5,000, 10,000, 25,000, 50,000, 100,000
and 250,000 USD of initial equity with nothing retuned (selection steps are
redone). Report gross, costs, cost as a share of equity, net return, net
Sharpe, maximum drawdown, and any column that explains what scales (minimum
tickets, integer contracts, margin cap). State what changes with capital and
what does not, and say whether the verdict changes. The headline uses the
100,000 USD for illustration.

## Before it goes in

Run `docs/audit_checklist.md` and `python tools/publish_gate.py`.
