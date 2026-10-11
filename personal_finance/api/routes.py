import io
from datetime import date
from typing import Annotated, Optional

import pandas as pd
import plotly.graph_objects as go
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, UploadFile
from python_calamine import CalamineError

from personal_finance.api.models import AccountInfo, BalancesTable, Summary, WorkbookMeta
from personal_finance.api.store import LoadedWorkbook
from personal_finance.data import create_accounts, create_holdings, read_workbook
from personal_finance.figures.account_line import plot_line_chart_account_plotly
from personal_finance.figures.balance_pie_chart import plot_account_balance_pie
from personal_finance.figures.holdings_analysis import (
    plot_covariance_heatmap,
    plot_tickers_evolution,
)
from personal_finance.figures.holdings_stacked import plot_holdings_stacked
from personal_finance.figures.monthly_bars import plot_monthly_diff_plotly, prepare_monthly_diff
from personal_finance.figures.stacked_accounts import plot_stacked_ts_balance_by_bank
from personal_finance.summary import active_tickers, compute_summary

# Endpoints are plain `def` so the blocking pandas and price-fetching work runs
# in FastAPI's thread pool instead of on the event loop.
router = APIRouter()


def current_workbook(request: Request, workbook_id: str) -> LoadedWorkbook:
    return request.app.state.store.get(workbook_id)


Workbook = Annotated[LoadedWorkbook, Depends(current_workbook)]


@router.post("/workbooks", status_code=201)
def upload_workbook(request: Request, file: UploadFile) -> WorkbookMeta:
    try:
        sheets = read_workbook(io.BytesIO(file.file.read()))
    except CalamineError:
        raise HTTPException(422, "Could not read the file as an Excel workbook.")

    try:
        accounts = create_accounts(sheets)
        holdings = create_holdings(sheets)
    except ValueError as error:
        # WorkbookValidationError messages already name the sheet, column and row.
        raise HTTPException(422, str(error))
    if not accounts:
        raise HTTPException(422, "The workbook has no 'Accounts' or 'Holdings' sheet.")

    accounts.calculate_balances()
    year_data = prepare_monthly_diff(accounts.merged_balances)
    workbook = request.app.state.store.put(accounts, holdings, year_data)
    return _meta(workbook)


def _meta(workbook: LoadedWorkbook) -> WorkbookMeta:
    mb = workbook.accounts.merged_balances
    months = mb.resample("ME").last().index
    return WorkbookMeta(
        id=workbook.id,
        accounts=[
            AccountInfo(
                id=acc.account_id,
                bank=acc.bank if isinstance(acc.bank, str) else None,
                type=acc.type,
                currency=acc.currency,
                status=acc.status,
            )
            for acc in workbook.accounts.values()
        ],
        date_min=mb.index.min().date(),
        date_max=mb.index.max().date(),
        years=sorted(workbook.year_data, reverse=True),
        months=[m.date() for m in sorted(months, reverse=True)],
        has_holdings="Holdings" in workbook.accounts,
    )


@router.get("/workbooks/{workbook_id}/summary")
def summary(workbook: Workbook) -> Summary:
    return Summary(**compute_summary(workbook.accounts))


@router.get("/workbooks/{workbook_id}/balances")
def balances(
    workbook: Workbook,
    start: Optional[date] = None,
    end: Optional[date] = None,
    accounts: Annotated[Optional[list[str]], Query()] = None,
) -> BalancesTable:
    mb = workbook.accounts.merged_balances
    if accounts is None:
        accounts = [a.account_id for a in workbook.accounts.values() if a.status == "Active"]
    unknown = [a for a in accounts if a not in workbook.accounts]
    if unknown:
        raise HTTPException(422, f"Unknown account(s): {', '.join(unknown)}")

    frame = (
        mb.loc[_ts(start):_ts(end), accounts]
        .sort_index(ascending=False)
        .rename_axis("date")
        .reset_index()
    )
    frame["date"] = frame["date"].dt.strftime("%Y-%m-%d")
    return BalancesTable(columns=list(frame.columns), rows=frame.to_dict("records"))


def _ts(value: Optional[date]) -> Optional[pd.Timestamp]:
    return pd.Timestamp(value) if value is not None else None


# --- Charts -----------------------------------------------------------------

def figure_response(fig: go.Figure) -> Response:
    # The frontend owns the theme, so drop the builder's template.
    fig.update_layout(template="none")
    return Response(fig.to_json(), media_type="application/json")


@router.get("/workbooks/{workbook_id}/charts/monthly-diff")
def monthly_diff_chart(workbook: Workbook, year: int) -> Response:
    if year not in workbook.year_data:
        raise HTTPException(422, f"No monthly data for {year}.")
    return figure_response(plot_monthly_diff_plotly(year, workbook.year_data[year]))


@router.get("/workbooks/{workbook_id}/charts/account-line")
def account_line_chart(workbook: Workbook, account: str = "total") -> Response:
    if account not in workbook.accounts.merged_balances.columns:
        raise HTTPException(422, f"Unknown account: {account}")
    return figure_response(plot_line_chart_account_plotly(workbook.accounts, account))


@router.get("/workbooks/{workbook_id}/charts/balance-treemap")
def balance_treemap_chart(workbook: Workbook, month: Optional[date] = None) -> Response:
    month = month or workbook.accounts.merged_balances.index.max().date()
    try:
        fig = plot_account_balance_pie(workbook.accounts, month)
    except ValueError as error:
        raise HTTPException(422, str(error))
    return figure_response(fig)


@router.get("/workbooks/{workbook_id}/charts/balances-by-bank")
def balances_by_bank_chart(workbook: Workbook) -> Response:
    return figure_response(plot_stacked_ts_balance_by_bank(workbook.accounts, None, None))


@router.get("/workbooks/{workbook_id}/charts/holdings-pnl")
def holdings_pnl_chart(workbook: Workbook) -> Response:
    if "Holdings" not in workbook.accounts:
        raise HTTPException(409, "This workbook has no holdings.")
    return figure_response(plot_holdings_stacked(workbook.accounts, None, None))


@router.get("/workbooks/{workbook_id}/charts/holdings-correlation")
def holdings_correlation_chart(workbook: Workbook) -> Response:
    tickers, _ = _tickers_or_409(workbook)
    return _price_figure(plot_covariance_heatmap(tickers))


@router.get("/workbooks/{workbook_id}/charts/holdings-evolution")
def holdings_evolution_chart(workbook: Workbook) -> Response:
    tickers, names = _tickers_or_409(workbook)
    return _price_figure(plot_tickers_evolution(tickers, names))


def _tickers_or_409(workbook: LoadedWorkbook) -> tuple[list[str], dict[str, str]]:
    # 409 rather than 404: the UI treats 404 as "workbook gone, upload again".
    tickers, names = active_tickers(workbook.holdings)
    if not tickers:
        raise HTTPException(409, "No current holdings to analyse.")
    return tickers, names


def _price_figure(fig: Optional[go.Figure]) -> Response:
    if fig is None:
        raise HTTPException(503, "Could not load prices.")
    return figure_response(fig)
