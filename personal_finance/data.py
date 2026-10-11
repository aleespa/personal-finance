import re
from pathlib import Path

import pandas as pd

from personal_finance.account import Account, AccountList
from personal_finance.holdings import get_historical_holdings
from personal_finance.schemas import (
    ACCOUNTS_SCHEMA,
    BALANCES_SCHEMA,
    HOLDINGS_SCHEMA,
    WorkbookValidationError,
    excel_rows,
    parse_dates,
    validate_sheet,
)


def create_holdings(table_path: Path):
    data = pd.read_excel(table_path, sheet_name=None, engine='calamine')
    if "Holdings" in data:
        return read_holdings(data["Holdings"])
    return None


def create_accounts(table_path: Path):
    data = pd.read_excel(table_path, sheet_name=None, engine='calamine')
    accounts_dict = {}

    if "Accounts" in data:
        accounts_table = parse_dates(
            _clean(data["Accounts"]), "Accounts", column="closed_date", required=False
        )
        accounts_table = validate_sheet(accounts_table, ACCOUNTS_SCHEMA, "Accounts")
        _check_status_matches_closed_date(accounts_table)

        for _, row in accounts_table.iterrows():
            account_id = row["account_id"]
            transactions = read_historical_data(data, account_id)
            closed_date = _closed_date(row, transactions)
            accounts_dict[account_id] = Account(
                account_id=account_id,
                bank=row["bank"],
                account_number=row.get("account_number"),
                type=row["type"],
                currency=row["currency"],
                status="Closed" if closed_date is not None else "Active",
                transactions=transactions,
                closed_date=closed_date,
            )

    if "Holdings" in data:
        transactions = get_historical_holdings(read_holdings(data["Holdings"]))
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


def _check_status_matches_closed_date(accounts_table: pd.DataFrame) -> None:
    if "status" not in accounts_table or "closed_date" not in accounts_table:
        return
    conflict = (accounts_table["status"] == "Active") & accounts_table["closed_date"].notna()
    if conflict.any():
        raise WorkbookValidationError(
            "Sheet 'Accounts' has accounts marked 'Active' that also have a "
            f"'Closed date' in Excel row(s) {excel_rows(accounts_table.index[conflict])}. "
            "Remove the date or set the status to 'Closed'."
        )


def _closed_date(row: pd.Series, transactions: pd.DataFrame):
    """Resolve when an account closed.

    An explicit 'Closed date' wins. An account marked 'Closed' without a date
    is treated as closed on the date of its last balance entry.
    """
    account_id = row["account_id"]
    closed_date = row.get("closed_date")
    if pd.notna(closed_date):
        late = transactions.index[transactions["date"] > closed_date]
        if len(late):
            raise WorkbookValidationError(
                f"Sheet '{account_id}' has balance entries after the account's "
                f"closed date {closed_date:%d/%m/%Y} in Excel row(s) {excel_rows(late)}."
            )
        return pd.Timestamp(closed_date)
    if row.get("status") == "Closed":
        return pd.Timestamp(transactions["date"].max())
    return None


def read_holdings(sheet: pd.DataFrame) -> pd.DataFrame:
    holdings = parse_dates(_clean(sheet), "Holdings")
    return validate_sheet(holdings, HOLDINGS_SCHEMA, "Holdings")


def read_historical_data(data: dict[str, pd.DataFrame], account_id: str) -> pd.DataFrame:
    if account_id not in data:
        raise WorkbookValidationError(
            f"Account '{account_id}' is listed in the Accounts sheet but has no "
            f"sheet named '{account_id}'."
        )
    transactions = parse_dates(_clean(data[account_id]), account_id)
    return validate_sheet(transactions, BALANCES_SCHEMA, account_id)


def _clean(sheet: pd.DataFrame) -> pd.DataFrame:
    # Excel files often contain formatted-but-empty rows after the actual
    # table. They are not data. The original index is kept so errors can
    # point at the right Excel row.
    return sheet.pipe(normalize_column_names).dropna(how="all")


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

