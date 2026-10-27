# Data schema: case 04

Three inputs are read from `$AUTOPSY_DATA_DIR`. In synthetic mode (`AUTOPSY_SYNTHETIC=1`) tables with the same columns are generated instead.

## Raw inputs
| file or folder | shape | content |
|---|---|---|
| `merged_forex_data_with_xauusd.csv` | wide, 1-minute | `timestamp`, then for each of 6 USD FX pairs `<PAIR>_final_df__bid_close` and `<PAIR>_final_df__ask_close` (float64); other columns are not read; naive timestamps, fixed UTC-5 offset (no daylight saving); sorted by time. Source: Interactive Brokers historical data API, `BID` and `ASK` bar series. Vendor terms: verify before publishing any value |
| `cftc_cot_fx/fut_fin_txt_<year>.zip` | one zip per year, text table inside | CFTC *Traders in Financial Futures* ("Financial Futures only") annual archive from the CFTC historical compressed files page. Columns read: `Market_and_Exchange_Names`, `Report_Date_as_YYYY-MM-DD`, `Open_Interest_All`, `Lev_Money_Positions_Long_All`, `Lev_Money_Positions_Short_All`. Public domain |
| `WS_CBPOL_csv_col.csv` | wide, daily columns | BIS central bank policy rates bulk file (`WS_CBPOL_csv_col`); columns read: `FREQ`, `REF_AREA`, `Series` and the daily date columns. Public |

## Tables the strategy consumes
Daily quotes (cached by the notebook as `fx_daily_bid_ask.parquet`):

| column | dtype | meaning | units |
|---|---|---|---|
| date | datetime | calendar day of the naive minute timestamp | day |
| asset | string | pair label | n/a |
| bid_close | float64 | last valid bid close of the day (rows with bid at or below zero or ask below bid are dropped first) | quote currency |
| ask_close | float64 | last valid ask close of the day | quote currency |

Positioning (one row per currency and report date):

| column | dtype | meaning | units |
|---|---|---|---|
| currency | string | one of seven currency codes, mapped from exact contract names | n/a |
| report_date | datetime | Tuesday of the position snapshot | day |
| open_interest | float64 | futures open interest | contracts |
| leveraged_long | float64 | leveraged-money long positions | contracts |
| leveraged_short | float64 | leveraged-money short positions | contracts |

Policy rates (one row per currency and observation day):

| column | dtype | meaning | units |
|---|---|---|---|
| currency | string | mapped from the BIS economy code (US, XM, GB, AU, CA, CH, JP) | n/a |
| observation_date | datetime | day of the daily series observation | day |
| policy_rate | float64 | policy rate | percent |

Keys: `(date, asset)`, `(currency, report_date)` and `(currency, observation_date)`; each unique and sorted ascending by its key. Null handling: invalid minute rows are dropped before the daily collapse; positioning rows with non-positive open interest or an unparsable date are dropped; empty rate cells are dropped; a duplicate currency and report date (or rate date) is a hard error. A missing CFTC archive year is a hard error, never fabricated.
Validate with `autopsy_common.schema.check_schema` (see the schema check cell in the notebook). The notebook prints pass/fail checks only (schema, key uniqueness, crossed quotes, currency mapping); no counts, dates, hashes or values.
