import unittest
from pathlib import Path
import pandas as pd

from personal_finance.data import create_accounts, create_holdings
from personal_finance.account import AccountList

class TestPersonalFinanceData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_path = Path("data/demo_data.xlsx")
        # Ensure path exists so tests fail gracefully if missing
        if not cls.data_path.exists():
            raise FileNotFoundError(f"Test data not found at {cls.data_path}")
            
    def test_create_holdings(self):
        """Test reading the holdings tab from excel."""
        holdings = create_holdings(self.data_path)
        self.assertIsNotNone(holdings)
        self.assertIn('isin', holdings.columns)
        self.assertIn('shares', holdings.columns)
        self.assertGreater(len(holdings), 0)

    def test_create_accounts(self):
        """Test account initialization and historical holdings computation."""
        accounts = create_accounts(self.data_path)
        self.assertIsInstance(accounts, AccountList)
        self.assertGreater(len(accounts), 0)
        
        # Verify Holdings account was generated correctly
        self.assertIn("Holdings", accounts.get_ids())
        holdings_acc = accounts.get_account("Holdings")
        
        # Important: these confirm the new features added for cost basis
        tx = holdings_acc.transactions
        self.assertIn("valuation", tx.columns)
        self.assertIn("balance", tx.columns)
        self.assertIn("date", tx.columns)
        
        # Verify calculation logics - valuations and balance shouldn't be null
        self.assertFalse(tx["valuation"].isnull().all())
        self.assertFalse(tx["balance"].isnull().all())
        
    def test_calculate_balances(self):
        """Test the merging process across all accounts."""
        accounts = create_accounts(self.data_path)
        accounts.calculate_balances()
        merged = accounts.merged_balances
        
        self.assertIsNotNone(merged)
        self.assertIn("total", merged.columns)
        self.assertIn("Holdings", merged.columns)
        
        # Ensure it creates a daily time series
        self.assertTrue(isinstance(merged.index, pd.DatetimeIndex))
        self.assertGreater(len(merged), 10) # Should have multiple days of data

if __name__ == '__main__':
    unittest.main()
