# Data schema: case 03

One raw input is read from `$AUTOPSY_DATA_DIR`; the notebook builds a small daily panel from it and caches the panel next to it. In synthetic mode (`AUTOPSY_SYNTHETIC=1`) a panel with the same columns is generated instead.

## Raw input
| file | shape | content |
|---|---|---|
| `merged_forex_data_with_xauusd.csv` | wide, 1-minute | `timestamp`, then for each of 6 USD FX pairs `<PAIR>_final_df__bid_close` and `<PAIR>_final_df__ask_close` (float64); the file also holds open, high and low columns that this case does not read; naive timestamps, fixed UTC-5 offset (no daylight saving); sorted by time |

Source: Interactive Brokers historical data API, FX contracts, `BID` and `ASK` bar series, one wide table. Vendor terms: verify before publishing any value.

## Daily panel (what the strategy consumes; cached as `fx_daily_bid_ask.parquet`)
| column | dtype | meaning | units |
|---|---|---|---|
| date | datetime | calendar day of the naive minute timestamp | day |
| asset | string | pair label | n/a |
| bid_close | float64 | last valid bid close of the day | quote currency |
| ask_close | float64 | last valid ask close of the day | quote currency |

Key: `(date, asset)`, sorted ascending by that tuple, one row per key. Null handling: minute rows with a missing bid or ask close are dropped before the daily collapse; duplicated minute timestamps keep the last row; the daily panel has no nulls and no crossed quotes (ask below bid is checked, not repaired). A pair can have a different set of dates from another pair; the pipeline aligns pairs only where it needs to.
Validate with `autopsy_common.schema.check_schema` (see the schema check cell in the notebook). The notebook prints pass/fail checks only (schema, nulls, key uniqueness and sort order, crossed quotes); no counts, dates, hashes or values.
