import unittest
from pathlib import Path

import pandas as pd

from personal_finance.data import create_accounts, create_holdings, read_workbook
from personal_finance.summary import active_tickers, compute_summary


class TestSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sheets = read_workbook(Path("data/demo_data.xlsx"))
        cls.accounts = create_accounts(sheets)
        cls.accounts.calculate_balances()
        cls.holdings = create_holdings(sheets)

    def test_compute_summary(self):
        summary = compute_summary(self.accounts)
        self.assertEqual(
            summary["active_accounts"] + summary["closed_accounts"], len(self.accounts)
        )
        self.assertIsNotNone(summary["unrealized_gains"])
        self.assertAlmostEqual(
            summary["total_balance"], self.accounts.merged_balances["total"].iloc[-1]
        )

    def test_delta_compares_totals(self):
        """The one-year change must not double-count the 'total' column."""
        mb = self.accounts.merged_balances
        past = mb.index.get_indexer(
            [mb.index[-1] - pd.DateOffset(years=1)], method="nearest"
        )[0]
        expected = mb["total"].iloc[-1] - mb["total"].iloc[past]
        self.assertAlmostEqual(compute_summary(self.accounts)["delta_1y"], expected)

    def test_active_tickers(self):
        tickers, names = active_tickers(self.holdings)
        self.assertGreater(len(tickers), 0)
        self.assertTrue(set(tickers) <= set(names))

    def test_active_tickers_without_holdings(self):
        self.assertEqual(active_tickers(None), ([], {}))


if __name__ == "__main__":
    unittest.main()
