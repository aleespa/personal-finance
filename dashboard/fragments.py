import streamlit as st

from personal_finance.figures.account_line import plot_line_chart_account_plotly
from personal_finance.figures.balance_pie_chart import plot_account_balance_pie
from personal_finance.figures.monthly_bars import plot_monthly_diff_plotly
from personal_finance.figures.stacked_accounts import plot_monthly_stacked_balance_by_bank_plotly


@st.fragment
def show_monthly_diff(year_data):
    if year_data:
        years = sorted(year_data.keys(), reverse=True)
        year = st.selectbox("Select a year", years)

        df = year_data[year]
        fig = plot_monthly_diff_plotly(year, df)
        st.plotly_chart(fig, use_container_width=True)

@st.fragment
def show_account_line(accounts):
    account_ids = sorted(accounts.get_ids())
    selected_account = st.selectbox("Select an account", account_ids)
    fig = plot_line_chart_account_plotly(accounts, selected_account)
    st.plotly_chart(fig, use_container_width=True)

@st.fragment
def show_balance_pie(accounts):
    monthly_dates = sorted(accounts.merged_balances.resample("ME").last().index.date, reverse=True)
    selected_date = st.selectbox("Select a month", monthly_dates)

    fig = plot_account_balance_pie(accounts, selected_date)
    st.plotly_chart(fig, use_container_width=True)

@st.fragment
def show_stacked_barchart(accounts, min_date, max_date, default_start, default_end):
    start_date, end_date = st.slider(
        "Select date range",
        min_value=min_date,
        max_value=max_date,
        value=(default_start, default_end),
        format="YYYY-MM-DD"
    )
    fig = plot_monthly_stacked_balance_by_bank_plotly(accounts, start_date, end_date)
    st.plotly_chart(fig, use_container_width=True)

@st.fragment
def show_transactions_fragment(accounts, min_date, max_date):
    active_cl = [account.account_id for account in accounts if account.status == "Active"]
    col1, col2, col3 = st.columns(3)
    date_range = col1.date_input("Date Range", [min_date, max_date])
    selected_accounts = col2.multiselect("Accounts", active_cl, default=active_cl)
    
    if len(date_range) == 2:
        st.dataframe(accounts.merged_balances.loc[date_range[0]:date_range[1], selected_accounts].sort_index(ascending=False))
