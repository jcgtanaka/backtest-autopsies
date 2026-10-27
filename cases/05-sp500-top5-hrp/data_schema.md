# Data schema: case 05

Two files are read from `$AUTOPSY_DATA_DIR`. In synthetic mode (`AUTOPSY_SYNTHETIC=1`) tables with the same shape are generated.

## `sp500_constituents.parquet` (membership)
| column | dtype | meaning | units |
|---|---|---|---|
| date | datetime | snapshot date on which the ticker was in the index | day |
| ticker | string | ticker symbol | n/a |

Source: public GitHub history `fja05680/sp500` (CC0), parsed so that a ticker with a `-YYYYMM` suffix stops at that month, then extended after its last snapshot from today's index list and announced changes. Key `(date, ticker)`, unique, sorted ascending. No nulls.

## `sp500_prices.parquet` (prices)
Wide table, index `Date` (datetime, unique, ascending), one float64 adjusted close column per ticker plus `SPY`. Source: Yahoo Finance via `yfinance`, downloaded by the reader. A ticker has nulls outside its trading life; gaps up to two days are forward-filled by the notebook, longer gaps are not. Vendor terms: verify before publishing any value.

Validate with `autopsy_common.schema.check_schema` (membership) and the checks in the notebook (prices). The notebook prints pass/fail checks only; no counts, dates, hashes or values.
