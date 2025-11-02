import tomllib
from datetime import datetime
from pathlib import Path

from personal_finance.data import create_accounts
from personal_finance.figures import plot_line_chart_account, plot_line_chart_all, plot_monthly_balance_bars, \
     plot_monthly_stacked_balance_by_bank


def main():
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)

    start_date = datetime(2020, 11, 1)
    end_date = datetime(2025, 10, 31)

    accounts = create_accounts(config["balance_table"])
    accounts.calculate_balances(start_date, end_date)
    # plot_line_chart_account(accounts, Path(config['outputs']) / "figures")
    plot_monthly_balance_bars(accounts, start_date, end_date, Path(config['outputs']) / "figures")
    plot_monthly_stacked_balance_by_bank(accounts, start_date, end_date, Path(config['outputs']) / "figures")
    plot_line_chart_all(accounts, start_date, end_date, Path(config['outputs']) / "figures")