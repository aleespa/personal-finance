import re
from pathlib import Path

import pandas as pd

from personal_finance.account import AccountList


def create_accounts(table_path: Path):
    accounts_table = (pd.read_excel(table_path, sheet_name="Accounts")
                      .pipe(normalize_column_names))

    accounts = AccountList.from_table(accounts_table)

    for account_id in accounts.get_ids():
        accounts[account_id].historical_data = read_historical_data(table_path, account_id)

    return accounts


def read_historical_data(table_path: Path, account_id: str) -> pd.DataFrame:
    try:
        return (
            pd.read_excel(table_path, sheet_name=account_id)
            .pipe(normalize_column_names)
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


def load_workbook(file):
    """
    Load an Excel workbook that contains:
    - A sheet 'accounts' with account metadata
    - A sheet 'transactions' with historical data
    """
    xls = pd.ExcelFile(file)

    accounts_df = pd.read_excel(xls, "Accounts").pipe(normalize_column_names)
    tx_df       = pd.read_excel(xls, "Transactions").pipe(normalize_column_names)

    account_list = AccountList.from_table(accounts_df)

    # Attach transaction data to each Account
    for acc in account_list.accounts:
        acc.historical_data = tx_df[tx_df["account_id"] == acc.account_id].copy()

    return account_list