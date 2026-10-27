# Data schema: case 01

File expected at `$AUTOPSY_DATA_DIR/daily_bars.parquet`. Source: minute bid/ask quotes for six USD-based FX pairs aggregated to daily bars with a fixed end-of-day cut (naive fixed UTC-5 clock); vendor: Interactive Brokers (FX bid/ask export); terms of use and redistribution rights are not verified.

| column | dtype | meaning | units |
|---|---|---|---|
| date | datetime64 | trading day | calendar date |
| asset | string | pair label (anonymised to P1..Pn inside the notebook) | n/a |
| asset_class | string | instrument group | n/a |
| high | float64 | highest mid of the day | quote currency |
| low | float64 | lowest mid of the day | quote currency |
| close | float64 | last mid of the day | quote currency |
| spread | float64 | mean bid-ask spread over the day's bars | quote currency |

Key: `(date, asset)`, sorted ascending by that tuple, one row per key. Rows without a close are dropped upstream; no nulls remain.
Validate with `autopsy_common.schema.check_schema` (see the schema check cell in the notebook, including the negative checks). The notebook prints pass/fail checks only (schema, nulls, key uniqueness and sort order); no counts, dates, hashes or values.
