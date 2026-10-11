# Angular UI — implementation plan

Spec: [docs/specs/2026-10-11-angular-ui-design.md](../specs/2026-10-11-angular-ui-design.md)

Work on a branch (`feature/angular-ui`). One commit per task. Run the full Python test
suite (`uv run python -m unittest discover tests`) at the end of every Python task;
Streamlit must keep working until Phase 5.

---

## Phase 1 — Decouple the package

### Task 1.1 — Remove Streamlit from `monthly_bars.py`
- Delete `import streamlit as st`, both `@st.cache_data` decorators and the unused
  `AccountList` import.
- Streamlit caching was only an optimisation; `prepare_monthly_diff` is cheap.
- Verify: `grep -r streamlit personal_finance/` returns nothing; tests pass.

### Task 1.2 — Read the workbook once
- `data.py`: add `read_workbook(source) -> dict[str, pd.DataFrame]` (the existing
  `pd.read_excel(..., sheet_name=None, engine='calamine')`).
- `create_accounts(source)` and `create_holdings(source)`: if `source` is a dict use it,
  otherwise call `read_workbook(source)`. Signatures stay backwards compatible, so
  tests, `debug.py` and `dashboard/app.py` keep working.
- `dashboard/app.py`: call `read_workbook` once and pass the dict to both.
- Test: add `test_read_workbook_once` in `tests/test_basic.py` that builds both from
  one dict and checks the results match the path-based calls.

### Task 1.3 — Extract summary logic
- New `personal_finance/summary.py`:
  - `compute_summary(accounts) -> dict` with the keys listed in the spec's `Summary`,
    logic moved verbatim from `fragments.show_summary` (including the
    nearest-date one-year delta and the Holdings unrealized-gains branch). Return plain
    Python floats/ints.
  - `active_tickers(holdings) -> tuple[list[str], dict[str, str]]` from
    `fragments.show_holdings_analysis` (tickers with positive summed shares, and the
    `yf_name -> full_name` map). Empty list when `holdings` is `None` or empty.
- `dashboard/fragments.py`: call these instead of the inline code.
- Tests: new `tests/test_summary.py` against the demo workbook: all keys present,
  `active_accounts + closed_accounts == number of accounts`, `unrealized_gains` not
  `None` for the demo data; `active_tickers(None) == ([], {})`.

### Task 1.4 — Holdings analysis download and bug fix
- `figures/holdings_analysis.py`:
  - `get_last_year_returns` returns `(pd.DataFrame(), pd.DataFrame())` when the download
    is empty (today it returns one DataFrame and callers fail to unpack).
  - Wrap the download in a cached helper keyed by `(tuple(sorted(tickers)), date.today())`
    using `functools.lru_cache(maxsize=8)` so the heatmap and evolution charts share
    one download per day. Return copies so callers can't mutate the cache.
- Test: patch `yf.download` to return an empty frame; both plot functions return
  `None` without raising; a second call does not hit the patched function again.

### Task 1.5 — Fixed file locations and dark-safe colours
- Add `PROJECT_ROOT = Path(__file__).resolve().parents[1]` in a small
  `personal_finance/paths.py`.
- `holdings.py`: cache at `PROJECT_ROOT / "price_cache.csv"`; write `holdings.csv` only
  if `os.environ.get("PF_DEBUG")`.
- `figures/balance_pie_chart.py`: read `PROJECT_ROOT / "bank_colors.json"`.
- `figures/account_line.py`: zero line `line_color="#888"` instead of black.
- Update CLAUDE.md and README notes about the CWD files.
- Verify: tests pass when run from the repo root; `PF_DEBUG=1 uv run python debug.py`
  still writes `holdings.csv`.

---

## Phase 2 — FastAPI backend

### Task 2.1 — Dependencies and packaging
- `uv add fastapi uvicorn python-multipart` (plus `httpx2` as a dev dependency for
  `TestClient`; Starlette 1.7 deprecates `httpx`).
- `pyproject.toml`: add a `[build-system]` (setuptools), set
  `include = ["personal_finance*"]` so subpackages are installed, and
  `[project.scripts] personal-finance = "personal_finance.api.main:main"`.
- Verify: `uv sync` succeeds and `uv run python -c "import personal_finance.api"` works.

### Task 2.2 — Store and app skeleton
- `personal_finance/api/store.py`: `LoadedWorkbook` dataclass (`id`, `accounts`,
  `holdings`, `year_data`) and a module-level `WorkbookStore` with `put(...) -> id`
  (replaces the previous one) and `get(id)` raising `HTTPException(404)` on a mismatch.
- `personal_finance/api/main.py`: `create_app()` mounting the router under `/api`;
  `main()` runs uvicorn on `127.0.0.1:8000` and opens the browser via
  `webbrowser.open` once the server is up (uvicorn `Server` in a thread or a startup
  hook).
- Pydantic response models in `personal_finance/api/models.py`: `AccountInfo`,
  `WorkbookMeta`, `Summary`, `BalancesTable`.

### Task 2.3 — Upload endpoint
- `POST /api/workbooks`: read `UploadFile` into `io.BytesIO`, `read_workbook`,
  `create_accounts`, `create_holdings`, `calculate_balances`, `prepare_monthly_diff`;
  store and return `WorkbookMeta` with status 201.
- `WorkbookValidationError` → `HTTPException(422, detail=str(error))`. A non-Excel file
  (calamine raises) → 422 "Could not read the file as an Excel workbook."
- Tests (`tests/test_api.py`, `TestClient`): demo upload returns 201 with
  `has_holdings == True` and all demo account ids; a workbook missing an account sheet
  returns 422 with the existing message; a text file returns 422.

### Task 2.4 — Summary and balances endpoints
- `GET /summary` → `compute_summary`.
- `GET /balances?start&end&accounts=` (repeatable `accounts`, default active
  accounts) → `{columns, rows}` with ISO dates, sorted newest first. Unknown account →
  422.
- Tests: summary keys match the model; balances filtered by date and account.

### Task 2.5 — Chart endpoints
- Helper `figure_response(fig)`: `fig.update_layout(template="none")`, return
  `Response(fig.to_json(), media_type="application/json")`.
- Routes per the spec, each calling the existing builder. Validate params (unknown
  year/account/month → 422). `holdings-*` routes return 409 when the workbook has no
  holdings (404 is reserved for unknown workbooks). Analysis routes return 503 when the builder returns `None`.
- Tests: every chart route returns JSON with `data` and `layout` for the demo
  workbook; bad params → 422; stale id → 404. Patch the yfinance download in the
  analysis-chart tests so they don't need the network.

### Task 2.6 — Static serving
- If `web/dist/web/browser/` exists, serve its files and return `index.html` for any
  GET that is not under `/api` and doesn't match a file (SPA fallback). If it's missing,
  `/` returns a short message saying to run `npm run build` in `web/`.
- Test: with a temporary dist folder, `/accounts` returns the `index.html` content and
  `/api/...` 404s are not swallowed by the fallback.

---

## Phase 3 — Angular scaffold and Overview

### Task 3.1 — Scaffold
- `npx @angular/cli@22 new web --routing --style=scss --ssr=false --skip-git`.
- `ng add @angular/material` (custom theme, no global typography override).
- `npm i plotly.js-dist-min@3.3.1` plus a local `src/types/plotly.d.ts` declaring
  the few functions used (`react`, `purge`, `Plots.resize`); the published `@types`
  don't track this version.
- `proxy.conf.json` mapping `/api` to `http://127.0.0.1:8000`; wire it into `ng serve`.
- `.gitignore`: `web/dist/`, `web/node_modules/`, `web/.angular/`.
- Verify: `npm run build` produces `web/dist/web/browser/index.html`; `uv run
  personal-finance` serves the starter page.

### Task 3.2 — Core services, theme and shell
- `models.ts` mirroring the Pydantic models.
- `ApiService` (HttpClient) and `WorkbookService` (`meta` signal, `clear()`).
- HTTP interceptor: on 404 from a `/api/workbooks/` URL, clear the workbook, navigate
  to `/upload` and show a snackbar.
- `ThemeService`: `mode` signal (`light | dark`), initial value from
  `prefers-color-scheme`, toggles a `dark` class on `<html>` that switches the Material
  theme.
- Shell: Material toolbar with title, tab nav (`mat-tab-nav-bar` + router links),
  theme toggle, "Upload new workbook" button. Investments link hidden unless
  `meta().has_holdings`.
- Routes with a guard redirecting to `/upload` when `meta()` is null; default route
  `/overview`.

### Task 3.3 — Upload page
- Drop zone + file input (`.xlsx`), spinner while the request runs, on success set
  `meta` and navigate to `/overview`.
- On 422 show the message as a list (split on newlines, strip leading `- `).
- Unit tests: success navigates; 422 renders the list; guard redirects without a
  workbook.

### Task 3.4 — `<app-plot>` and `<app-chart-card>`
- `<app-plot [figure]>`: on figure or theme change, `Plotly.react(el, data,
  merge(layout, overlay(theme)), {responsive: true, displaylogo: false})`;
  `ResizeObserver` → `Plots.resize`; `Plotly.purge` on destroy.
- Overlay: transparent `paper_bgcolor` and `plot_bgcolor`, font colour, x/y
  `gridcolor` and `zerolinecolor` from CSS variables of the Material theme, and a
  colorway. Remove the figure's fixed `height` so the card controls size.
- `<app-chart-card>`: title, content projection for controls, states loading /
  error / ready. Takes an `Observable` or resource of the figure.

### Task 3.5 — Overview tab
- KPI cards (Material cards in a responsive grid) from `/summary`, formatted as GBP.
- Treemap card with a month select (from `meta().months`).
- Monthly-diff card with a year select (from `meta().years`).
- Total balance line (`account-line?account=total`).
- Verify in the browser with the demo workbook, light and dark.

---

## Phase 4 — Remaining tabs

### Task 4.1 — Accounts tab
- Account line card with an account select (`total` + sorted account ids).
- Balances-by-bank card; enable `xaxis.rangeslider` in the frontend overlay for this
  chart (input flag on `<app-plot>`).

### Task 4.2 — Investments tab
- Holdings P&L card with the range slider.
- Correlation heatmap and ticker evolution cards; 503 shows "Could not load prices".

### Task 4.3 — Transactions tab
- `npm i ag-grid-community ag-grid-angular`; register `AllCommunityModule`.
- Material date-range picker (defaults to `date_min..date_max`) and account
  multi-select (defaults to active accounts) → `/balances`.
- AG Grid with the date column pinned left, GBP formatting, AG Grid's dark theme when
  `ThemeService.mode() === 'dark'`.

### Task 4.4 — Parity check
- Walk through every Streamlit section side by side with the Angular app on the demo
  workbook: same numbers in KPI cards, same charts, same table rows.
- Check a workbook without a `Holdings` sheet (Investments tab hidden, no errors) and
  a broken workbook (errors listed).

---

## Phase 5 — Launch, docs, remove Streamlit

### Task 5.1 — Remove Streamlit
- Delete `dashboard/`.
- `uv remove streamlit streamlit-aggrid streamlit-extras`.
- Remove the `template="plotly_white"` from the builders now that only the API
  uses them (the API helper still forces `"none"`).
- Verify: `grep -ri streamlit` only hits docs history; all tests pass.

### Task 5.2 — Docs
- README: new "Running" section (`cd web && npm ci && npm run build`, then
  `uv run personal-finance`), development mode (`uv run uvicorn
  personal_finance.api.main:create_app --factory --reload` + `npm start` in `web/`),
  features list updated for the tabs.
- CLAUDE.md: commands, architecture (API + Angular), test commands for both sides.

### Task 5.3 — Final verification
- Fresh clone simulation: `uv sync`, `npm ci`, `npm run build`, `uv run
  personal-finance`, upload the demo workbook, click through every tab in both themes.
- `uv run python -m unittest discover tests` and `npm test` both pass.
