import pandera.pandas as pa
from collections import UserDict
from dataclasses import dataclass, field
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
    transactions: pd.DataFrame
    balance: Optional[pd.DataFrame] = None

    def __post_init__(self):
        schema = pa.DataFrameSchema(
            {
                "date": pa.Column(pa.DateTime),
                "balance": pa.Column(float, coerce=True, nullable=True),
                "transaction_number": pa.Column(float, coerce=True, nullable=True),
            },
            strict=False,
        )
        self.transactions = schema.validate(self.transactions)

    def calculate_balance(self, start_date: str, end_date: str):
        self.transactions['date'] = pd.to_datetime(self.transactions.date, dayfirst=False).dt.date
        df_sorted = self.transactions.sort_values(['date', 'transaction_number'], ascending=[True, False])
        balance = df_sorted.drop_duplicates(subset='date', keep='first')
        balance = balance.sort_values('date')[['date', 'balance']].reset_index(drop=True)
        full_dates = pd.date_range(start=start_date, end=end_date)
        balance = balance.set_index('date').reindex(full_dates)
        balance.index.name = 'date'
        self.balance = (
            balance
            .ffill()
            .reset_index()
            .rename(columns={'balance': self.account_id}, inplace=False)
        )


class AccountList(UserDict):
    def __init__(self, accounts: dict[str, Account] = None):
        super().__init__(accounts or {})
        self.merged_balances: Optional[pd.DataFrame] = None

    def get_ids(self) -> list[str]:
        return list(self.data.keys())

    def get_account(self, account_id: str) -> Account:
        return self.data[account_id]

    def calculate_balances(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        if not self.data:
            self.merged_balances = pd.DataFrame()
            return
            
        if start_date is None:
            start_date = min([min(acc.transactions.date.to_list()) for acc in self.data.values()])
        if end_date is None:
            end_date = max([max(acc.transactions.date.to_list()) for acc in self.data.values()])
            
        for account in self.data.values():
            account.calculate_balance(start_date, end_date)

        self.merge_balances()

    def merge_balances(self):
        frames = []
        for account in self.data.values():
            if account.balance is not None:
                balance = account.balance[['date', account.account_id]]
                frames.append(balance.set_index('date'))

        if not frames:
            return
            
        merged_balances = pd.concat(frames, axis=1, join='outer')
        merged_balances.index = pd.to_datetime(merged_balances.index)
        full_dates = pd.date_range(merged_balances.index.min(), merged_balances.index.max())
        merged_balances = (
            merged_balances.reindex(full_dates)
            .rename_axis('date')
            .fillna(0)
            .ffill()
        )
        merged_balances['total'] = merged_balances.sum(axis=1)

        self.merged_balances = merged_balances

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.data.values())[key]
        return super().__getitem__(key)




