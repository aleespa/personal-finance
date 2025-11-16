import os
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import pandas as pd
import plotly.graph_objects as go
from matplotlib import pyplot as plt
import streamlit as st

from personal_finance.account import AccountList

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


def plot_line_chart_account(accounts: AccountList, filepath: Path):
    rolling_avg = accounts.merged_balances.rolling(window=7, min_periods=1).mean()

    for account_id in accounts.get_ids():
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)

        x = rolling_avg.index
        y = rolling_avg[account_id].fillna(0)  # Handle NaNs for plotting

        ax.fill_between(x, y, 0, where=(y >= 0), interpolate=True, color='green', alpha=0.5)
        ax.fill_between(x, y, 0, where=(y < 0), interpolate=True, color='red', alpha=0.5)

        ax.set_title(account_id, fontsize=12, loc='left')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_ylim(bottom=0 if (y >= 0).all() else None)

        # Format y-axis as £Xk
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"£{x / 1000:,.1f}k"))
        ax.set_ylabel('Balance')
        ax.axhline(0, color='black', linewidth=0.8, linestyle='--', alpha=0.4)
        ax.grid(which='major', alpha=0.3)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlabel("Date")
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[3, 9]))
        ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
        ax.tick_params(axis='x', which='minor', labelsize=9)

        # Save to file with account name (safe filename)
        safe_name = (account_id
                     .replace("-", "_")
                     .replace("/", "_")
                     .replace("\\", "_")
                     .replace(" ", "_"))
        plt.tight_layout()
        plt.savefig(os.path.join(filepath, f"{safe_name}.png"), dpi=300)


def plot_line_chart_all(
        accounts: AccountList,
        start_date,
        end_date,
        filepath: Path):
    rolling_avg = accounts.merged_balances.rolling(window=14, min_periods=1).mean()

    plt.figure(figsize=(14, 6), dpi=100)
    plt.plot(rolling_avg.index, rolling_avg['total'], lw=2, color='k')

    plt.xlabel('Date')
    plt.ylabel('Balance')

    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    formatter = mtick.FuncFormatter(lambda x, _: f"£{x / 1000:,.0f}k")
    ax.yaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # Minor x-axis: April, July, October
    minor_locator = mdates.MonthLocator(bymonth=[4, 7, 10])
    minor_formatter = mdates.DateFormatter('%b')
    ax.xaxis.set_minor_locator(minor_locator)
    ax.xaxis.set_minor_formatter(minor_formatter)
    ax.tick_params(axis='x', which='minor', labelsize=8, rotation=0)
    ax.grid(which='major', linestyle='--', alpha=0.2)
    ax.grid(which='minor', linestyle=':', alpha=0.5)
    ax.set_xlim(start_date, end_date + pd.DateOffset(days=5))
    ax.axhline(0, color='gray', lw=1)

    ax.fill_between(
        rolling_avg.index,
        rolling_avg.total,
        0,
        where=(rolling_avg.total >= 0),
        interpolate=True,
        color='green',
        alpha=0.2
    )
    ax.fill_between(
        rolling_avg.index,
        rolling_avg.total,
        0,
        where=(rolling_avg.total < 0),
        interpolate=True,
        color='red',
        alpha=0.2
    )

    plt.tight_layout()

    plt.savefig(filepath / "Total balance.png", dpi=300)

def plot_monthly_balance_bars(accounts, start_date, end_date, filepath: Path):
    """
    Plot a monthly bar chart of balances for each account between start_date and end_date.

    Parameters
    ----------
    accounts : AccountList
        Object containing .merged_balances (DataFrame with date index and one column per account)
    start_date, end_date : datetime-like
        Range of interest
    filepath : Path
        Directory where to save plots
    """

    # Ensure date index
    df = accounts.merged_balances.copy()
    df = df.loc[start_date:end_date]

    # Compute month-end balances
    monthly = df.resample('ME').last()

    # Create a bar chart for each account
    for col in monthly.columns:
        balances = monthly[col]
        colors = ['green' if val >= 0 else 'red' for val in balances]
        fig, ax = plt.subplots(1,1, figsize=(10, 5), dpi=100)
        ax.bar(balances.index, balances, width=20, zorder=1, color=colors)  # ~20 days wide bars

        ax.set_xlabel("Month")
        ax.set_ylabel("Balance")

        ax.spines[['top', 'right']].set_visible(False)

        formatter = mtick.FuncFormatter(lambda x, _: f"£{x / 1000:,.1f}k")
        ax.yaxis.set_major_formatter(formatter)

        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))  # every 3 months
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))

        ax.grid(axis='y', linestyle='--', alpha=0.3, zorder=0)
        ax.axhline(0, color='gray', lw=1)

        plt.tight_layout()
        # Save figure
        plt.savefig(filepath / f"{col}_Monthly_Balance.png", dpi=300)
        plt.close()

def plot_monthly_stacked_balance_by_bank(accounts, start_date, end_date, filepath: Path):
    """
    Plot a diverging stacked monthly bar chart of balances for all accounts (excluding 'total'),
    with colors based on the bank each account belongs to.
    Positive balances stack upward; negative balances stack downward.
    """

    df = accounts.merged_balances.copy().loc[start_date:end_date]

    # Exclude the total column if present
    if "total" in df.columns:
        df = df.drop(columns="total")

    # Resample to month-end (use .last() to get end-of-month balances)
    monthly = df.resample("ME").last()

    # Map each account_id to its bank
    account_to_bank = {acc.account_id: acc.bank for acc in accounts.accounts}

    # Get unique banks and assign distinct colors
    unique_banks = list({acc.bank for acc in accounts.accounts if acc.bank})
    cmap = plt.get_cmap("tab10")
    bank_colors = {bank: cmap(i % 10) for i, bank in enumerate(unique_banks)}
    account_colors = {acc.account_id: bank_colors.get(acc.bank, "gray") for acc in accounts.accounts}

    # --- Plot setup ---
    plt.figure(figsize=(14, 7), dpi=100)
    bottom_pos = pd.Series(0, index=monthly.index)  # For positive stacks
    bottom_neg = pd.Series(0, index=monthly.index)  # For negative stacks

    for col in monthly.columns:
        values = monthly[col].fillna(0)
        color = account_colors.get(col, "gray")

        # Split positive and negative parts
        pos_values = values.clip(lower=0)
        neg_values = values.clip(upper=0)

        # Plot positives (above zero)
        plt.bar(
            monthly.index,
            pos_values,
            bottom=bottom_pos,
            color=color,
            width=20,
            label=f"{col} ({account_to_bank.get(col, 'Unknown')})"
        )
        bottom_pos += pos_values

        # Plot negatives (below zero)
        plt.bar(
            monthly.index,
            neg_values,
            bottom=bottom_neg,
            color=color,
            width=20
        )
        bottom_neg += neg_values

    # --- Styling ---
    plt.title("Monthly Balances by Account (Positive/Negative Stacked by Bank)", fontsize=14)
    plt.xlabel("Month")
    plt.ylabel("Balance")

    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Format y-axis as £xk
    formatter = mtick.FuncFormatter(lambda x, _: f"£{x / 1000:,.0f}k")
    ax.yaxis.set_major_formatter(formatter)

    # Format x-axis (every 3 months)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))

    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.axhline(0, color="gray", lw=1)
    plt.legend(title="Account (Bank)", bbox_to_anchor=(1.05, 1), loc="upper left")

    plt.tight_layout()
    plt.savefig(filepath / "Monthly_Stacked_Balances_by_Bank.png", dpi=300)
    plt.close()

def plot_monthly_diff(accounts: AccountList,  filepath: Path):
    monthly_df = monthly_balance_difference(accounts.merged_balances)
    monthly_df = monthly_df.sort_index().dropna(subset=['monthly_diff'])

    years = monthly_df.index.get_level_values("year").unique()
    for year in years:
        yearly = monthly_df.xs(year, level="year")
        y = yearly["monthly_diff"].to_numpy()
        dates = [
            pd.Timestamp(year=year, month=mo, day=15)
            for mo in yearly.index
        ]
        colors = ['tab:green' if v >= 0 else 'tab:red' for v in y]
        fig, ax = plt.subplots(figsize=(14, 6))
        width = pd.Timedelta(days=20)
        ax.bar(dates, y, width=width, color=colors, align='center', zorder=1)
        ax.set_xlabel("Month")
        ax.set_ylabel("Balance Difference")
        fig.autofmt_xdate()
        ax.grid(True, axis="y", linestyle="--", alpha=0.3, zorder=0)
        ax.spines[["top", "right"]].set_visible(False)
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.6)
        formatter = mtick.FuncFormatter(lambda x, _: f"£{x / 1000:,.1f}k")
        ax.yaxis.set_major_formatter(formatter)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
        ax.set_xlim(pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31"))
        ax.set_ylim(min(-1_200, y.min()-100), max(5_000, y.max()+100))
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(filepath / f"Monthly diff {year}", bbox_inches="tight")
        plt.close(fig)

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