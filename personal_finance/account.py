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
    balance: Optional[pd.DataFrame] = None

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

    def calculate_balance(
            self,
            start_date: str,
            end_date: str):
        self.historical_data['date'] = pd.to_datetime(self.historical_data.date, dayfirst=True).dt.date
        df_sorted = self.historical_data.sort_values(['date', 'transaction_number'], ascending=[True, False])
        balance = df_sorted.drop_duplicates(subset='date', keep='first')
        balance = balance.sort_values('date')[['date', 'balance']].reset_index(drop=True)
        full_dates = pd.date_range(start=start_date, end=end_date)
        balance = balance.set_index('date').reindex(full_dates)
        balance.index.name = 'date'
        self.balance = (balance
                        .ffill()
                        .reset_index()
                        .rename(columns={'balance': self.account_id}, inplace=False))

@dataclass
class AccountList:
    accounts: list[Account]
    merged_balances: Optional[pd.DataFrame] = None

    @classmethod
    def from_tables(cls, accounts: pd.DataFrame | None = None, holdings: pd.DataFrame | None = None):
        if accounts is not  None:
            accounts = [Account.from_row(row) for _, row in accounts.iterrows()]
        if holdings is not None:
            holdings = Account(
                account_id="Holdings",
                bank=None,
                account_number=None,
                type="Investment",
                currency="GBP",
                status="Active",
            )
            return cls(accounts + [holdings])
        return cls(accounts)

    def get_ids(self) -> list[str]:
        return [a.account_id for a in self.accounts]

    def calculate_balances(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None):
        if start_date is None:
            start_date = min([min(acc.historical_data.date.to_list()) for acc in self.accounts])
        if end_date is None:
            end_date = max([max(acc.historical_data.date.to_list()) for acc in self.accounts])
        for account in self.accounts:
            account.calculate_balance(start_date, end_date)

        self.merge_balances()

    def merge_balances(self):
        frames = []
        for account in self.accounts:
            balance = account.balance[['date', account.account_id]]
            frames.append(balance.set_index('date'))

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



