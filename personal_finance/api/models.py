from datetime import date
from typing import Optional

from pydantic import BaseModel


class AccountInfo(BaseModel):
    id: str
    bank: Optional[str]
    type: str
    currency: str
    status: str


class WorkbookMeta(BaseModel):
    id: str
    accounts: list[AccountInfo]
    date_min: date
    date_max: date
    years: list[int]
    months: list[date]
    has_holdings: bool


class Summary(BaseModel):
    total_balance: float
    delta_1y: float
    total_credit: float
    active_accounts: int
    closed_accounts: int
    debit_accounts: int
    credit_accounts: int
    transactions: int
    unrealized_gains: Optional[float]


class BalancesTable(BaseModel):
    columns: list[str]
    rows: list[dict[str, float | str]]
