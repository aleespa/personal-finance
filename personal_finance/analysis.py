import tomllib
from datetime import datetime

from personal_finance.data import create_accounts


def main():
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)

    start_date = datetime(2020, 11, 1)
    end_date = datetime(2025, 8, 2)

    accounts = create_accounts(config["balance_table"])
    accounts.calculate_balances(start_date, end_date)
