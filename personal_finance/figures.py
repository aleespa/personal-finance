import os
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import pandas as pd
from matplotlib import pyplot as plt

from personal_finance.account import AccountList


def plot_line_chart_account(accounts: AccountList, filepath: Path):
    rolling_avg = accounts.merged_balances.rolling(window=14, min_periods=1).mean()

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
