import pandas as pd
import streamlit as st

from personal_finance.figures.account_line import plot_line_chart_account_plotly
from personal_finance.figures.balance_pie_chart import plot_account_balance_pie
from personal_finance.figures.monthly_bars import plot_monthly_diff_plotly
from personal_finance.figures.stacked_accounts import plot_stacked_ts_balance_by_bank
from personal_finance.figures.holdings_stacked import plot_holdings_stacked
from personal_finance.figures.holdings_analysis import plot_covariance_heatmap, plot_tickers_evolution


@st.fragment
def show_summary(accounts):
    st.subheader("Summary")
    latest = accounts.merged_balances.iloc[-1, :-1]
    active_acc = len([accounts for account in accounts if account.status == "Active"])
    closed_acc = len([accounts for account in accounts if account.status != "Active"])
    total_balance = latest.sum()
    total_credit = latest[latest < 0].sum()
    positive_accounts = (latest > 0).sum()
    negative_accounts = (latest < 0).sum()

    one_year_ago_date = accounts.merged_balances.index[-1] - pd.DateOffset(years=1)
    past_idx = accounts.merged_balances.index.get_indexer(
        [one_year_ago_date], method="nearest"
    )[0]
    balance_1yr_ago = accounts.merged_balances.iloc[past_idx].sum()
    delta_balance = total_balance - balance_1yr_ago

    number_transactions = sum(len(acc.historical_data) for acc in accounts)

    colA, colB, colC, colD = st.columns(4)
    colA.metric(
        "Total Balance",
        f"£{total_balance:,.0f}",
        delta=f"{delta_balance:,.0f}",
    )
    colA.metric("Total Credit", f"£{-total_credit:,.0f}")
    colB.metric("Active Accounts", active_acc)
    colB.metric("Closed Accounts", closed_acc)
    colC.metric("Debit Accounts", positive_accounts)
    colC.metric("Credit Accounts", negative_accounts)
    colD.metric("Number of transactions", f"{number_transactions:,.0f}")


@st.fragment
def show_monthly_diff(year_data):
    if year_data:
        years = sorted(year_data.keys(), reverse=True)
        year = st.selectbox("Select a year", years)

        df = year_data[year]
        fig = plot_monthly_diff_plotly(year, df)
        st.plotly_chart(fig, width='stretch')


@st.fragment
def show_account_line(accounts):
    account_ids = sorted(accounts.get_ids())
    selected_account = st.selectbox("Select an account", account_ids)
    fig = plot_line_chart_account_plotly(accounts, selected_account)
    st.plotly_chart(fig, width='stretch')


@st.fragment
def show_balance_pie(accounts):
    monthly_dates = sorted(accounts.merged_balances.resample("ME").last().index.date,
                           reverse=True)
    selected_date = st.selectbox("Select a month", monthly_dates)

    fig = plot_account_balance_pie(accounts, selected_date)
    st.plotly_chart(fig, width='stretch')


@st.fragment
def show_stacked_barchart(accounts, min_date, max_date, default_start, default_end):
    start_date, end_date = st.slider(
        "Select date range",
        min_value=min_date,
        max_value=max_date,
        value=(default_start, default_end),
        format="YYYY-MM-DD"
    )
    fig = plot_stacked_ts_balance_by_bank(accounts, start_date, end_date)
    st.plotly_chart(fig, width='stretch')



@st.fragment
def show_transactions_fragment(accounts, min_date, max_date):
    active_cl = [account.account_id for account in accounts if account.status == "Active"]
    col1, col2, col3 = st.columns(3)
    date_range = col1.date_input("Date Range", [min_date, max_date])
    selected_accounts = col2.multiselect("Accounts", active_cl, default=active_cl)

    if len(date_range) == 2:
        st.dataframe(accounts.merged_balances.loc[
            date_range[0]:date_range[1], selected_accounts].sort_index(
            ascending=False))


@st.fragment
def show_holdings_stacked(accounts, min_date, max_date, default_start, default_end):
    if "Holdings" not in accounts.get_ids():
        return
    st.subheader("Holdings Evolution")
    start_date, end_date = st.slider(
        "Select date range for Holdings",
        min_value=min_date,
        max_value=max_date,
        value=(default_start, default_end),
        format="YYYY-MM-DD",
        key="holdings_slider"
    )
    fig = plot_holdings_stacked(accounts, start_date, end_date)
    if fig:
        st.plotly_chart(fig, width='stretch')


@st.fragment
def show_holdings_analysis(holdings):
    if holdings is None or holdings.empty:
        return

    st.subheader("Holdings Analysis")

    df = holdings.copy()
    
    # We normalized column names in create_holdings, so they are snake_case now.
    date_col = "date"
    yf_name_col = "yf_name"
    full_name_col = "full_name"
    shares_col = "shares"

    df[date_col] = pd.to_datetime(df[date_col])
    
    # Latest holdings are those where cumulative shares > 0.
    latest_holdings = df.groupby(yf_name_col)[shares_col].sum()
    active_tickers = latest_holdings[latest_holdings > 0].index.tolist()
    
    if not active_tickers:
        st.write("No active holdings found for analysis.")
        return

    names_dict = df.set_index(yf_name_col)[full_name_col].to_dict()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("### Covariance Heatmap")
        fig_cov = plot_covariance_heatmap(active_tickers)
        if fig_cov:
            st.plotly_chart(fig_cov, width='stretch')
        else:
            st.write("Could not load covariance data.")

    with col2:
        st.write("### Ticker Evolution")
        fig_evol = plot_tickers_evolution(active_tickers, names_dict)
        if fig_evol:
            st.plotly_chart(fig_evol, width='stretch')
        else:
            st.write("Could not load evolution data.")

    with col3:
        st.write("### Stats")
        # Left unimplemented as requested
        st.write("Summary statistics (to be implemented)")
