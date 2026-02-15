import re
from pathlib import Path

import pandas as pd

from personal_finance.account import AccountList
from personal_finance.holdings import get_historical_holdings


def create_accounts(table_path: Path):
    data = pd.read_excel(table_path, sheet_name=None)
    if "Accounts" in data:
        accounts_table = data["Accounts"].pipe(normalize_column_names)
    else:
        accounts_table = None
    if "Holdings" in data:
        holdings = data["Holdings"].pipe(normalize_column_names)
    else:
        holdings = None

    accounts = AccountList.from_tables(accounts_table, holdings)

    for account_id in accounts.get_ids():
        accounts[account_id].historical_data = read_historical_data(table_path, account_id)

    accounts["Holdings"].historical_data = get_historical_holdings(holdings).pipe(normalize_column_names)

    return accounts


def read_historical_data(table_path: Path, account_id: str) -> pd.DataFrame:
    try:
        return (
            pd.read_excel(table_path, sheet_name=account_id)
            .pipe(normalize_column_names)
            .assign(date=lambda x: pd.to_datetime(x.date, dayfirst=True))
        )
    except KeyError:
        raise ValueError(f"No data found for account_id='{account_id}'")


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [to_snake_case(col) for col in df.columns]
    return df


def to_snake_case(name: str) -> str:
    name = re.sub(r'[^0-9a-zA-Z]+', '_', name)
    name = name.lower()
    name = re.sub(r'^_+|_+$', '', name)
    if re.match(r'^\d', name):
        name = f'col_{name}'
    return name

