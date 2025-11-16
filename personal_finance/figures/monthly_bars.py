import pandas as pd

from personal_finance.account import AccountList

import plotly.graph_objects as go
import streamlit as st

@st.cache_data
def plot_monthly_diff_plotly(year: int, df: pd.DataFrame):
    y = df["monthly_diff"].to_numpy()
    months = df.index.to_numpy()

    dates = [
        pd.Timestamp(year=year, month=int(mo), day=15)
        for mo in months
    ]

    colors = ["green" if v >= 0 else "red" for v in y]

    fig = go.Figure(
        data=[
            go.Bar(
                x=dates,
                y=y,
                marker_color=colors,
                hovertemplate="<b>%{x|%b %Y}</b><br>Δ £%{y:,.0f}<extra></extra>"
            )
        ]
    )

    fig.update_layout(
        title=f"Monthly Balance Difference — {year}",
        xaxis_title="Month",
        yaxis_title="Balance Difference (£)",
        template="plotly_white",
        height=500,
    )

    fig.update_xaxes(
        dtick="M1",
        tickformat="%b<br>%Y",
        range=[f"{year}-01-01", f"{year}-12-31"],
    )

    fig.update_yaxes(tickprefix="£")

    return fig

@st.cache_data
def prepare_monthly_diff(accounts: AccountList):
    """Return a dict of {year: df} ready for plotting in Streamlit."""
    df = monthly_balance_difference(accounts.merged_balances)
    df = df.sort_index().dropna(subset=["monthly_diff"])

    # Extract years safely even if index level name is unknown
    if hasattr(df.index, "names") and "year" in df.index.names:
        years = df.index.get_level_values("year").unique()
    else:
        # fallback if index levels aren't named
        years = df.index.get_level_values(0).unique()

    year_data = {}
    for year in years:
        if "year" in df.index.names:
            sub = df.xs(year, level="year")
        else:
            sub = df.loc[year]  # fallback

        year_data[int(year)] = sub.copy()

    return year_data

def monthly_balance_difference(df):
    """
    End-of-month balances + continuous month-to-month differences.
    January difference is computed from previous December.
    """
    df = df.copy()
    df.index = pd.to_datetime(df.index)

    # Extract year & month
    df['year'] = df.index.year
    df['month'] = df.index.month

    # End-of-month value
    monthly = df.groupby(['year', 'month'])['total'].last()

    # Continuous difference with no reset at January
    monthly_diff = monthly.diff()

    return pd.DataFrame({
        'monthly_total': monthly,
        'monthly_diff': monthly_diff
    })