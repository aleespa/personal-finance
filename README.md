# Personal Finance Dashboard

A local web app for visualizing personal finance data. You upload an Excel workbook with your accounts, their balance history and, optionally, your investment transactions. The app builds a daily balance history across all accounts and renders interactive Plotly charts.

It runs on your machine only: a FastAPI server (`personal_finance/api/`) processes the workbook in memory and serves an Angular UI (`web/`). Nothing is stored after the server stops, so you upload the workbook each time.

## Features

* Upload an Excel workbook with accounts, balance histories and investment holdings
* Daily balance history per account and in total, forward-filled between entries
* Four tabs of interactive Plotly charts:
  * **Overview:** summary figures (total balance, year-on-year change, unrealized gains, credit), balance by bank for a chosen month, monthly balance change per year, total balance over time
  * **Accounts:** any account's balance over time, month-end balances stacked by bank with a range slider
  * **Investments** (only with a `Holdings` sheet): unrealized gain/loss per holding over time, last-year volatility/correlation heatmap and indexed price evolution
  * **Transactions:** table of daily balances filtered by date range and account
* Light and dark themes (follows your OS, with a toggle)
* Workbook problems listed on upload with the sheet, column and Excel row
* Historical prices for holdings fetched automatically and cached locally
* Bank brand colors configurable in `bank_colors.json`

## Installation

Requires:

* Python 3.13+ and [uv](https://docs.astral.sh/uv/)
* Node.js 24 (or 22.22+) to build the web UI. `web/.node-version` pins 24 for version managers such as [fnm](https://github.com/Schniz/fnm).

```bash
git clone <repository_url>
cd personal-finance
uv sync
cd web
npm ci
npm run build
```

Rebuild the UI (`npm run build` in `web/`) after pulling frontend changes. The build output in `web/dist/` is not committed.

With fnm on Windows, run the npm commands through the pinned version, e.g. `fnm exec --using=24 -- npm.cmd ci`.

### Optional: EODHD API key

Holding prices are fetched from Yahoo Finance first. For assets Yahoo doesn't cover, the app falls back to [EODHD](https://eodhd.com/) by ISIN. To enable it, create a `.env` file in the project root:

```
EODHD_API_KEY=your_key_here
```

If neither source has a price, the transaction price is used.

## Data Format

The dashboard expects an `.xlsx` workbook. Column headers are case- and spacing-insensitive (`Account id` and `account_id` both work). See `data/demo_data.xlsx` for a complete example.

The workbook is checked when you upload it. If a sheet has problems, the dashboard lists all of them at once, with the column, the offending value and the Excel row number. Fully empty rows are ignored.

### 1. `Accounts` sheet

| Account id | Bank     | Account number | Type    | Currency | Closed date |
| ---------- | -------- | -------------- | ------- | -------- | ----------- |
| Barclays   | Barclays | 12345678       | Current | GBP      |             |
| Revolut    | Revolut  | 98765432       | Savings | GBP      | 31/03/2024  |

* `Type` must be one of: `Current`, `Savings`, `Credit Card`, `Loan`, `Investment`
* `Currency` must be `GBP` or `MXN`
* `Account id` must be unique. `Account number` is optional.
* `Closed date` is optional. Leave it blank for open accounts. After that date the account's balance counts as zero, and no balance entries may come after it.
* `Status` is optional and can be `Active` or `Closed`. An account is closed when it has a `Closed date`. An account marked `Closed` without a date is treated as closed on the date of its last balance entry. An account marked `Active` can't have a `Closed date`.

### 2. One sheet per account

Each account needs its own sheet, named exactly like its `Account id`.

| Date       | Balance | Transaction number |
| ---------- | ------- | ------------------ |
| 01/01/2025 | 1000    | 1                  |
| 02/01/2025 | 1200    | 2                  |
| 02/01/2025 | 1150    | 3                  |

* `Date` is read day-first (`DD/MM/YYYY`) when it is text. Every row must have a valid date.
* `Balance` is the account balance after that transaction. It must be a number and can't be blank.
* When a day has several rows, the row with the highest `Transaction number` is that day's closing balance.

### 3. `Holdings` sheet (optional)

One row per buy or sell of an investment.

| Date       | Full name            | ISIN         | YF name  | Transaction type | Shares | Price  | Amount |
| ---------- | -------------------- | ------------ | -------- | ---------------- | ------ | ------ | ------ |
| 15/03/2025 | Vanguard FTSE All-World | IE00BK5BQT80 | VWRP.L   | Buy              | 10     | 110.50 | 1105   |

* `Date`, `Full name`, `ISIN`, `Shares` and `Price` are required. `Price` can't be negative.
* `Shares` is negative for sells.
* `YF name` is the Yahoo Finance ticker. Leave it blank to rely on EODHD.
* Prices are converted to GBP. Invested amount uses the average-cost method.

The holdings appear as an extra account named `Holdings`.

## Running the App

From the project root:

```bash
uv run personal-finance
```

This starts the server on `http://127.0.0.1:8000` and opens it in your browser. Options: `--port 8080` to use another port, `--no-browser` to skip opening a tab. Stop it with Ctrl+C.

## Development

For hot reload while changing the UI, run the API and the Angular dev server side by side:

```bash
uv run uvicorn personal_finance.api.main:create_app --factory --reload   # API on :8000
cd web && npm start                                                       # UI on :4200, proxies /api to :8000
```

Tests:

```bash
uv run python -m unittest discover tests                 # Python tests (run from the repo root)
cd web && npx ng test --watch=false                       # Angular unit tests
uv run python debug.py --workbook data/demo_data.xlsx    # print each pipeline stage
```

The API's interactive docs are at `http://127.0.0.1:8000/docs` while the server runs.

## Notes

* Fetched prices are cached in `price_cache.csv` in the project root. Delete it, or rows from it, to force a refetch.
* Set the `PF_DEBUG` environment variable to write a debug dump of computed holdings to `holdings.csv` in the project root.
* MXN balances are not converted to GBP. Totals add all accounts as-is.
