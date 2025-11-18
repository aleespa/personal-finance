import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import streamlit as st

from personal_finance.figures.monthly_bars import (
    plot_monthly_diff_plotly, prepare_monthly_diff
)
from personal_finance.figures.account_line import (
    plot_line_chart_account_plotly
)

from personal_finance.figures.balance_pie_chart import plot_account_balance_pie
from personal_finance.figures.stacked_accounts import plot_monthly_stacked_balance_by_bank_plotly

from personal_finance.data import create_accounts

st.set_page_config(page_title="Finance Dashboard", layout="wide")
st.title("📊 Personal Finance Dashboard")

uploaded_file = st.file_uploader("Upload workbook", type=["xlsx"])

# Initialize session state
if "accounts" not in st.session_state:
    st.session_state.accounts = None

if "year_data" not in st.session_state:
    st.session_state.year_data = None

if uploaded_file:
    accounts = create_accounts(uploaded_file)
    st.session_state.accounts = accounts

if st.session_state.accounts:
    accounts = st.session_state.accounts
    accounts.calculate_balances()
    st.session_state.year_data = prepare_monthly_diff(accounts)

    st.subheader("Summary")
    latest = accounts.merged_balances.iloc[-1, :-1]
    active_acc = len([accounts for account in accounts if account.status == "Active"])
    closed_acc = len([accounts for account in accounts if account.status != "Active"])
    total_balance = latest.sum()
    total_credit = latest[latest < 0].sum()
    positive_accounts = (latest > 0).sum()
    negative_accounts = (latest < 0).sum()

    one_year_ago_date = accounts.merged_balances.index[-1] - pd.DateOffset(years=1)
    past_idx = accounts.merged_balances.index.get_indexer([one_year_ago_date], method="nearest")[0]
    balance_1yr_ago = accounts.merged_balances.iloc[past_idx].sum()
    delta_balance = total_balance - balance_1yr_ago

    number_transactions = sum(len(acc.historical_data) for acc in accounts)

    colA, colB, colC, colD = st.columns(4)
    colA.metric("Total Balance", f"£{total_balance:,.0f}", delta=f"{delta_balance:,.0f}", )
    colA.metric("Total Credit", f"£{-total_credit:,.0f}")
    colB.metric("Active Accounts", active_acc)
    colB.metric("Closed Accounts", closed_acc)
    colC.metric("Debit Accounts", positive_accounts)
    colC.metric("Credit Accounts", negative_accounts)
    colD.metric("Number of transactions", f"{number_transactions:,.0f}")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.session_state.year_data:
            year_data = st.session_state.year_data
            years = sorted(year_data.keys(), reverse=True)
            year = st.selectbox("Select a year", years)

            df = year_data[year]
            fig = plot_monthly_diff_plotly(year, df)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        account_ids = sorted(accounts.get_ids())
        selected_account = st.selectbox("Select an account", account_ids)
        fig = plot_line_chart_account_plotly(accounts, selected_account)
        st.plotly_chart(fig, use_container_width=True)
    with col3:
        monthly_dates = sorted(accounts.merged_balances.resample("ME").last().index.date, reverse=True)
        selected_date = st.selectbox("Select a month", monthly_dates)

        fig = plot_account_balance_pie(accounts, selected_date)
        st.plotly_chart(fig, use_container_width=True)

    min_date = pd.to_datetime("2020-01-01").date()
    max_date = pd.to_datetime("today").date()

    # Default values as datetime.date
    default_start = min_date
    default_end = max_date

    start_date, end_date = st.slider(
        "Select date range",
        min_value=min_date,
        max_value=max_date,
        value=(default_start, default_end),
        format="YYYY-MM-DD"
    )
    fig = plot_monthly_stacked_balance_by_bank_plotly(accounts, start_date, end_date)
    st.plotly_chart(fig, use_container_width=True)

    st.table(accounts.merged_balances.tail(10))