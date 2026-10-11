# Angular UI — design spec

Date: 2026-10-11
Status: approved

## Goal

Replace the Streamlit dashboard with a custom Angular web UI. The user uploads the
workbook and explores the charts. The Python package keeps all data processing and
chart building; Angular only renders.

## Decisions

| Topic | Decision |
|---|---|
| Deployment | Local only, single user, no auth. Binds to `127.0.0.1`. |
| Persistence | None. The workbook lives in memory; upload on every start. |
| Charts | Existing Plotly builders, sent as figure JSON (`fig.to_json()`), rendered with plotly.js. Dash is not used. |
| plotly.js version | Pinned to the version bundled with the Python `plotly` package (3.3.1 for plotly 6.5.2). |
| Component library | Angular Material. AG Grid for the balances table. |
| Layout | Tabbed pages: Overview, Accounts, Investments, Transactions. |
| Theme | Light and dark, follows the OS by default, toolbar toggle. Charts restyle with the theme. |
| Upload wait | Single blocking request with a spinner. |
| Launch | `uv run personal-finance` starts the server, serves the built Angular app and opens the browser. |
| Streamlit | Kept working during the migration, removed once the Angular UI has parity. |

## Architecture

```
Angular app (web/) ──POST /api/workbooks──────────► FastAPI (personal_finance/api/)
                   ◄── workbook metadata                │
                   ──GET /api/workbooks/{id}/...──►     ├─► personal_finance pipeline
                   ◄── summary / figure JSON / rows     └─► personal_finance/figures/*
```

In production FastAPI serves `web/dist/web/browser/` and falls back to `index.html`
for any non-`/api` path so deep links (`/accounts`) work. In development `ng serve`
proxies `/api` to `127.0.0.1:8000`.

## Repo layout

```
personal_finance/
  summary.py        KPI and active-holdings logic (moved out of dashboard/fragments.py)
  api/
    main.py         app factory, static serving, main() entry point
    routes.py       endpoints
    store.py        in-memory workbook store
web/                Angular app; dist/ is git-ignored
docs/specs/, docs/plans/
```

## API

All endpoints are under `/api`. Endpoints are sync `def` so the blocking pandas and
network work runs in FastAPI's thread pool.

| Method & path | Response |
|---|---|
| `POST /workbooks` (multipart `file`) | `201` `WorkbookMeta`; `422` `{detail: <validation message>}` |
| `GET /workbooks/{id}/summary` | `Summary` |
| `GET /workbooks/{id}/charts/monthly-diff?year=` | figure JSON |
| `GET /workbooks/{id}/charts/account-line?account=` | figure JSON |
| `GET /workbooks/{id}/charts/balance-treemap?month=` | figure JSON |
| `GET /workbooks/{id}/charts/balances-by-bank` | figure JSON (full range) |
| `GET /workbooks/{id}/charts/holdings-pnl` | figure JSON (full range) |
| `GET /workbooks/{id}/charts/holdings-correlation` | figure JSON; `503` if prices can't be fetched |
| `GET /workbooks/{id}/charts/holdings-evolution` | figure JSON; `503` if prices can't be fetched |
| `GET /workbooks/{id}/balances?start=&end=&accounts=` | `{columns: [...], rows: [...]}`, newest first |

- `WorkbookMeta`: `id`, `accounts[{id, bank, type, currency, status}]`, `date_min`,
  `date_max`, `years` (desc), `months` (month-end dates, desc), `has_holdings`.
- `Summary`: `total_balance`, `delta_1y`, `total_credit`, `active_accounts`,
  `closed_accounts`, `debit_accounts`, `credit_accounts`, `transactions`,
  `unrealized_gains` (nullable).
- The store holds only the most recent workbook. Any other `id` returns `404`; the UI
  then returns to the upload screen. Because of that, `404` is reserved for unknown
  workbooks: holdings charts on a workbook with no (current) holdings return `409`.
- Figure JSON is produced by one helper that sets `template="none"` before
  `to_json()`, so the frontend owns the theme. Builders keep their template for
  Streamlit until it is removed.
- Date ranges are not API parameters: the two time-range charts get Plotly's range
  slider and are filtered in the browser.

## Frontend

- Routes: `/upload`, `/overview`, `/accounts`, `/investments`, `/transactions`. A guard
  redirects to `/upload` when no workbook is loaded. The Investments tab is hidden
  when `has_holdings` is false.
- `WorkbookService`: current `WorkbookMeta` as a signal. `ApiService`: typed HTTP calls.
- `<app-plot>`: wraps `plotly.js-dist-min` (`Plotly.react`, `ResizeObserver`), merges
  a light or dark layout overlay (backgrounds, font and grid colours, colorway) derived
  from the Material theme, and re-renders when the theme changes.
- `<app-chart-card>`: Material card with title, controls slot, loading spinner and
  error message.
- Tabs:
  - Overview: KPI cards, balance treemap + month picker, monthly-diff bars + year
    picker, total balance line.
  - Accounts: account line + account picker, balances by bank with range slider.
  - Investments: holdings P&L with range slider, correlation heatmap, ticker evolution.
  - Transactions: AG Grid with date-range and account filters (active accounts by
    default).
- Toolbar: app title, tab nav, theme toggle, "Upload new workbook".
- Upload page: drag-and-drop or file picker (`.xlsx`), spinner while processing,
  validation errors shown as a list (the 422 message split on newlines).

## Python package changes

- `figures/monthly_bars.py`: drop the `streamlit` import and `@st.cache_data`.
- `data.py`: add `read_workbook(source)` returning the parsed sheets dict;
  `create_accounts` and `create_holdings` accept either a path/file or that dict, so
  the API reads the file once.
- `summary.py`: `compute_summary(accounts)` and `active_tickers(holdings)`.
- `figures/holdings_analysis.py`: download last-year prices once per ticker set and
  day (shared by both charts); fix `get_last_year_returns` returning a single empty
  DataFrame where callers unpack two values.
- `figures/account_line.py`: zero line uses a neutral grey that works on dark.
- `holdings.py`: `price_cache.csv` resolved from the project root;
  `holdings.csv` written only when `PF_DEBUG` is set.
- `figures/balance_pie_chart.py`: `bank_colors.json` resolved from the project root.

## Error handling

- Workbook validation: `422`, message shown on the upload page.
- Unknown workbook id: `404`, UI navigates to `/upload` with a snackbar.
- Holdings chart on a workbook with no holdings, or none still held: `409`, message in
  the chart card.
- Price download failure for analysis charts: `503`, chart card shows
  "Could not load prices"; the rest of the page still works.
- Unexpected errors: `500`, chart card shows a generic error.

## Testing

- Backend: `unittest` + FastAPI `TestClient` against `data/demo_data.xlsx`: upload,
  422 on a broken workbook, 404 on a stale id, every chart endpoint returns `data` and
  `layout`, summary and balances shapes. Existing tests keep passing.
- Frontend: unit tests for the upload flow and the route guard; manual browser check
  of every tab in light and dark.

## Out of scope

Auth, remote deployment, persistence, FX conversion for MXN accounts, upload progress
steps, new chart types.
