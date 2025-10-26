import re
from pathlib import Path

import pandas as pd

from personal_finance.account import Account, AccountList


def create_accounts(table_path: Path):
    accounts_table = (pd.read_excel(table_path, sheet_name="Accounts")
                      .pipe(normalize_column_names))

    accounts = AccountList.from_table(accounts_table)

    for account_id in accounts.get_ids():
        try:
            accounts[account_id].historical_data = (
                pd.read_excel(table_path, sheet_name=account_id)
                .pipe(normalize_column_names)
            )
        except KeyError:
            raise ValueError(f"No data found for account_id='{account_id}'")

    return accounts

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
