from dataclasses import dataclass
from typing import Optional, Literal

import pandas as pd


@dataclass
class Account:
    account_id: str
    bank: Optional[str]
    account_number: Optional[str]
    type: Literal["Current", "Savings", "Credit Card", "Loan", "Investment"]
    currency: Literal["MXN", "GBP"]
    status: Literal["Active", "Closed"]
    historical_data: Optional[pd.DataFrame] = None

    @classmethod
    def from_row(cls, row):
        return cls(
            account_id=row["account_id"],
            bank=row["bank"],
            account_number=row["account_number"],
            type=row["type"],
            currency=row["currency"],
            status=row["status"],
        )

@dataclass
class AccountList:
    accounts: list[Account]

    @classmethod
    def from_table(cls, table: pd.DataFrame):
        return cls([Account.from_row(row) for _, row in table.iterrows()])

    def get_ids(self) -> list[str]:
        return [a.account_id for a in self.accounts]

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.accounts[key]

        elif isinstance(key, str):
            for account in self.accounts:
                if account.account_id == key:
                    return account
            raise KeyError(f"No account found with account_id='{key}'")
        else:
            raise TypeError("Key must be int (index) or str (account_id)")

    def __len__(self):
        return len(self.accounts)


