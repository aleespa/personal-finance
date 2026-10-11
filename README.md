# Personal Finance Dashboard

A Streamlit dashboard for visualizing personal finance data. You upload an Excel workbook with your accounts, their balance history and, optionally, your investment transactions. The app builds a daily balance history across all accounts and renders interactive Plotly charts.

## Features

* Upload an Excel workbook with accounts, balance histories and investment holdings
* Daily balance history per account and in total, forward-filled between entries
* Interactive Plotly charts:
  * Summary metrics (total balance, year-on-year change, unrealized gains) and balance distribution by bank
  * Monthly balance differences per year
  * Individual account balances over time
  * Stacked balances by bank for a selected date range
  * Unrealized gain/loss per holding over time
  * Last-year normalized price evolution and a variance/correlation heatmap for current holdings
* Filterable table of daily balances by account and date range
* Historical prices for holdings fetched automatically and cached locally
* Bank brand colors configurable in `bank_colors.json`

## Installation

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repository_url>
cd personal-finance
uv sync
```

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

| Account id | Bank     | Account number | Type    | Currency | Status |
| ---------- | -------- | -------------- | ------- | -------- | ------ |
| Barclays   | Barclays | 12345678       | Current | GBP      | Active |
| Revolut    | Revolut  | 98765432       | Savings | GBP      | Active |

* `Type` must be one of: `Current`, `Savings`, `Credit Card`, `Loan`, `Investment`
* `Currency` must be `GBP` or `MXN`
* `Status` must be `Active` or `Closed`
* `Account id` must be unique. `Account number` is optional.

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

## Running the Dashboard

From the project root:

```bash
uv run streamlit run dashboard/app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`) and upload your workbook.

## Development

```bash
uv run python -m unittest discover tests      # run the tests
uv run python debug.py --workbook data/demo_data.xlsx   # print each pipeline stage
```

## Notes

* Fetched prices are cached in `price_cache.csv` in the working directory. Delete it, or rows from it, to force a refetch.
* A debug dump of computed holdings is written to `holdings.csv` in the working directory.
* MXN balances are not converted to GBP. Totals add all accounts as-is.
