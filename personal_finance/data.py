import re
from pathlib import Path

import pandas as pd

from personal_finance.account import Account, AccountList
from personal_finance.holdings import get_historical_holdings


def create_holdings(table_path: Path):
    data = pd.read_excel(table_path, sheet_name=None)
    if "Holdings" in data:
        holdings = data["Holdings"].pipe(normalize_column_names)
        return holdings
    return None

def create_accounts(table_path: Path):
    data = pd.read_excel(table_path, sheet_name=None)
    accounts_dict = {}

    if "Accounts" in data:
        accounts_table = data["Accounts"].pipe(normalize_column_names)
        for _, row in accounts_table.iterrows():
            account_id = row["account_id"]
            transactions = read_historical_data(table_path, account_id)
            accounts_dict[account_id] = Account(
                account_id=account_id,
                bank=row["bank"],
                account_number=row["account_number"],
                type=row["type"],
                currency=row["currency"],
                status=row["status"],
                transactions=transactions,
            )

    if "Holdings" in data:
        holdings_table = data["Holdings"].pipe(normalize_column_names)
        transactions = get_historical_holdings(holdings_table)
        accounts_dict["Holdings"] = Account(
            account_id="Holdings",
            bank=None,
            account_number=None,
            type="Investment",
            currency="GBP",
            status="Active",
            transactions=transactions,
        )

    return AccountList(accounts_dict)


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

