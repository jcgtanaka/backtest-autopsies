# Data schema: case 06

One raw input is read from `$AUTOPSY_DATA_DIR`; the notebook builds a small daily panel from it and caches the panel next to it. In synthetic mode (`AUTOPSY_SYNTHETIC=1`) a panel with the same columns is generated instead.

## Raw input
| file | shape | content |
|---|---|---|
| `merged_crypto_1min.parquet` | wide, 1-minute | `timestamp`, then per coin (bch, btc, eth, ltc, sol) `<coin>_open/high/low/close/volume/bar_count/average/symbol/exchange`; this case reads only close, high and low; naive timestamps, fixed UTC-5 offset (no daylight saving) |

Source: Interactive Brokers historical data API, crypto contracts routed to a crypto venue, `TRADES` bars. Vendor terms: verify before publishing any value.

## Daily panel (what the strategy consumes; cached as `crypto_daily_panel.parquet`)
| column | dtype | meaning | units |
|---|---|---|---|
| date | datetime | calendar day of the naive minute timestamp | day |
| asset | string | coin label | n/a |
| close | float64 | last valid close of the day | USD |
| high | float64 | maximum high of the day | USD |
| low | float64 | minimum low of the day | USD |

Key: `(date, asset)`, sorted ascending by that tuple, one row per key. Null handling: days with no valid close for a coin are dropped for that coin (a coin has no rows before it was listed); the last valid close of a day is used so a newly listed coin's first day resolves to its real price. Validate with `autopsy_common.schema.check_schema` (see the schema check cell in the notebook). The notebook prints pass/fail checks only (schema, key uniqueness and sort order, nulls, high/close/low ordering); no counts, dates, hashes or values.
