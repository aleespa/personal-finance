# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Python dependencies are managed with `uv` (Python >= 3.13, see `.python-version`). The Angular app in `web/` needs Node 24 (`web/.node-version`); on this machine Node 24 comes from fnm, so run npm/ng as `fnm exec --using=24 -- npm.cmd ...` / `npx.cmd ng ...` (fnm on Windows doesn't resolve `.cmd` shims).

```bash
uv sync                                   # install Python deps into .venv
cd web && npm ci && npm run build         # build the UI into web/dist/web/browser
uv run personal-finance                   # serve API + built UI on http://127.0.0.1:8000 and open the browser (--port, --no-browser)
uv run uvicorn personal_finance.api.main:create_app --factory --reload  # API only, with reload
cd web && npm start                       # Angular dev server on :4200, proxies /api to :8000
uv run python -m unittest discover tests  # all Python tests
uv run python -m unittest tests.test_basic.TestPersonalFinanceData.test_create_accounts  # single test
cd web && npx ng test --watch=false       # Angular unit tests (Vitest)
uv run python debug.py --workbook data/demo_data.xlsx  # print each stage of the data pipeline
```

There is no linter or formatter configured for Python (`web/` has Prettier settings). Python tests use `unittest` and must be run from the repo root because they load `data/demo_data.xlsx` via a relative path.

## Architecture

A local, single-user web app: an Angular UI (`web/`) talks to a FastAPI server (`personal_finance/api/`) that wraps a plain-Python package (`personal_finance/`). The user uploads an Excel workbook; everything is derived from it in memory and nothing persists. Design and decisions: `docs/specs/2026-10-11-angular-ui-design.md`.

### Workbook format (actual, as read by the code)

Parsed in `personal_finance/data.py`:

- **`Accounts`** sheet: columns `Account id, Bank, Type, Currency`, plus optional `Account number`, `Status` and `Closed date`. `Account.status` is derived, not read: an account is `Closed` iff it resolves a `closed_date` (explicit `Closed date`, or the last balance entry when `Status` is `Closed` without a date). `calculate_balance` sets the balance to 0 after `closed_date`.
- **One sheet per account**, named exactly after its `Account id`, with `Date, Balance, Transaction number`. Dates are parsed `dayfirst=True`; a blank/invalid date raises `ValueError` naming the Excel row.
- Optional **`Holdings`** sheet: `Date, Full name, ISIN, YF name, Transaction type, Shares, Price, Amount` (one row per buy/sell; sells have negative shares).

All column headers are normalized to snake_case via `normalize_column_names` before use. Every sheet is then validated against a Pandera schema in `personal_finance/schemas.py` (`validate_sheet`, lazy mode). Failures raise `WorkbookValidationError`, a `ValueError` subclass that the upload endpoint returns as a 422 whose `detail` the upload page lists line by line. Messages use the human header and the one-based Excel row, which relies on keeping the original `read_excel` index (only fully empty rows are dropped). Add new required columns or allowed values to the schemas there. Excel is read with `engine='calamine'`. `data/demo_data.xlsx` is the reference example.

### Data flow

1. `data.read_workbook(source)` parses every sheet once; `create_accounts` and `create_holdings` accept either that dict or a path/file. `create_accounts` builds an `AccountList` (a `UserDict` of `account_id -> Account`). Each `Account` dataclass re-validates its `transactions` DataFrame against `BALANCES_SCHEMA` in `__post_init__`, which also covers the synthetic Holdings account.
2. If a `Holdings` sheet exists, `holdings.get_historical_holdings` turns it into a synthetic `Account` with id `"Holdings"` (type `Investment`, GBP). Its daily `transactions` frame has `balance` = invested cost basis (average-cost method), `valuation` = market value, plus per-asset `<name>_valuation`, `<name>_invested` and unrealized-P&L columns.
3. `AccountList.calculate_balances()` computes a daily forward-filled balance per account (last transaction of each day = the one with the highest `transaction_number`) and merges them into `merged_balances`: a daily `DatetimeIndex` frame with one column per account plus `total`.
4. `POST /api/workbooks` (`personal_finance/api/routes.py`) runs steps 1-3 once and keeps the result in `WorkbookStore` (`api/store.py`), which holds only the latest workbook; any other id gets 404. Endpoints are sync `def` so pandas and price fetching run in the thread pool.
5. Each chart endpoint calls a Plotly builder in `personal_finance/figures/` and returns `fig.to_json()` with `template="none"`; the frontend owns the theme. Headline KPIs and the list of still-held tickers come from `personal_finance/summary.py`. Gain/loss colours live in `figures/colors.py`. All charts are Plotly; there is no matplotlib code.

### API conventions

- 404 is reserved for "unknown workbook" (the UI's interceptor then sends the user back to upload), so holdings charts on a workbook without current holdings return 409. 422 is bad input or an invalid workbook; 503 means prices couldn't be downloaded.
- `create_app(frontend_dir=...)` serves `web/dist/web/browser` with an `index.html` fallback for deep links; with no build it serves a short "run npm run build" page. Tests pass `frontend_dir=None`.
- The yfinance download for the holdings analysis charts is cached per ticker set and day in `figures/holdings_analysis.py` (`_PRICE_CACHE`); tests clear it and patch `yf.download`.

### Frontend (`web/`)

Angular 22 (standalone components, signals, zoneless) with Angular Material 3. `WorkbookService` holds the uploaded workbook's metadata in a signal (lost on reload by design); pages fetch with `httpResource` via `WorkbookService.request(path, params)`. `<app-plot>` lazy-loads `plotly.js-dist-min` (pinned to 3.3.1, the plotly.js version the Python `plotly` package targets; keep them in step) and merges `themedLayout()` from `shared/chart-theme.ts`, which holds the validated categorical palette and chart chrome per theme. `<app-chart-card>` wraps a chart with loading/error states. The Transactions tab uses AG Grid. Light/dark is `ThemeService` setting `color-scheme` on `<html>`; Material's tokens follow via `light-dark()`.

### Price fetching and side-effect files

`get_historical_holdings` fetches daily close prices per ISIN only for dates where shares are held:
- Primary source is yfinance using the `yf_name` column; prices are converted to GBP (GBp is divided by 100, other currencies use `<CCY>GBP=X` FX rates).
- Fallback is EODHD by ISIN, which needs `EODHD_API_KEY` in a `.env` file.
- Remaining gaps fall back to the transaction price (cost basis).
- Results, including NaN markers for dates that could not be fetched, are cached in `price_cache.csv` in the repo root (`personal_finance.paths.PROJECT_ROOT`). Delete rows from it to force a refetch. When the `PF_DEBUG` environment variable is set, the function also writes `holdings.csv` to the repo root as a debug dump. Both files are untracked.

All monetary values are effectively treated as GBP; there is no FX conversion for MXN accounts.

### Scratch scripts

`main.py` is a scratch script that runs the holdings pipeline and copies the result to the clipboard. `debug.py` prints each pipeline stage for a workbook.

### Styling

`bank_colors.json` maps bank names to brand hex colors; `figures/balance_pie_chart.py` reads it from the repo root as an override for chart colors.
