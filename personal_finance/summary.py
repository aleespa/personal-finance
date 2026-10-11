from typing import Optional

import pandas as pd

from personal_finance.account import AccountList


def compute_summary(accounts: AccountList) -> dict:
    """Headline figures for the latest day of ``accounts.merged_balances``.

    ``calculate_balances`` must have been called first.
    """
    mb = accounts.merged_balances
    latest = mb.drop(columns="total").iloc[-1]

    one_year_ago = mb.index[-1] - pd.DateOffset(years=1)
    past_idx = mb.index.get_indexer([one_year_ago], method="nearest")[0]

    return {
        "total_balance": float(latest.sum()),
        "delta_1y": float(mb["total"].iloc[-1] - mb["total"].iloc[past_idx]),
        "total_credit": float(-latest[latest < 0].sum()),
        "active_accounts": sum(acc.status == "Active" for acc in accounts.values()),
        "closed_accounts": sum(acc.status != "Active" for acc in accounts.values()),
        "debit_accounts": int((latest > 0).sum()),
        "credit_accounts": int((latest < 0).sum()),
        "transactions": sum(len(acc.transactions) for acc in accounts.values()),
        "unrealized_gains": _unrealized_gains(accounts),
    }


def _unrealized_gains(accounts: AccountList) -> Optional[float]:
    if "Holdings" not in accounts:
        return None
    transactions = accounts["Holdings"].transactions
    if transactions.empty or not {"valuation", "balance"} <= set(transactions.columns):
        return None
    latest = transactions.iloc[-1]
    return float(latest["valuation"] - latest["balance"])


def active_tickers(holdings: Optional[pd.DataFrame]) -> tuple[list[str], dict[str, str]]:
    """Yahoo Finance tickers still held, and a ``yf_name -> full_name`` map.

    ``holdings`` is the validated Holdings sheet from ``create_holdings``.
    """
    if holdings is None or holdings.empty:
        return [], {}
    shares = holdings.groupby("yf_name")["shares"].sum()
    names = holdings.set_index("yf_name")["full_name"].to_dict()
    return shares[shares > 0].index.tolist(), names
