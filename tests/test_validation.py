import tempfile
import unittest
from pathlib import Path

import pandas as pd

from personal_finance.data import create_accounts, create_holdings
from personal_finance.schemas import WorkbookValidationError


def accounts_sheet(**overrides):
    row = {
        "Account id": "Bank A",
        "Bank": "Barclays",
        "Account number": 12345678,
        "Type": "Current",
        "Currency": "GBP",
        "Status": "Active",
    }
    row.update(overrides)
    return pd.DataFrame([row])


def balances_sheet():
    return pd.DataFrame(
        {
            "Date": ["01/01/2025", "02/01/2025"],
            "Balance": [100.0, 120.0],
            "Transaction number": [1, 2],
        }
    )


def holdings_sheet(**overrides):
    row = {
        "Date": "15/03/2025",
        "Full name": "Fund",
        "ISIN": "GB00BJS8SJ34",
        "YF name": "0P000125KV.L",
        "Transaction type": "Buy",
        "Shares": 10,
        "Price": 3.5,
        "Amount": 35,
    }
    row.update(overrides)
    return pd.DataFrame([row])


class WorkbookTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "book.xlsx"

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, sheets: dict[str, pd.DataFrame]):
        with pd.ExcelWriter(self.path) as writer:
            for name, df in sheets.items():
                df.to_excel(writer, sheet_name=name, index=False)
        return self.path

    def assert_error(self, sheets, *fragments, loader=create_accounts):
        with self.assertRaises(WorkbookValidationError) as ctx:
            loader(self.write(sheets))
        message = str(ctx.exception)
        for fragment in fragments:
            self.assertIn(fragment, message)
        return message


class TestWorkbookValidation(WorkbookTestCase):
    def test_valid_workbook_loads(self):
        accounts = create_accounts(
            self.write({"Accounts": accounts_sheet(), "Bank A": balances_sheet()})
        )
        self.assertEqual(accounts.get_ids(), ["Bank A"])

    def test_numeric_account_id_matches_sheet(self):
        accounts = create_accounts(
            self.write({"Accounts": accounts_sheet(**{"Account id": 123}), "123": balances_sheet()})
        )
        self.assertEqual(accounts.get_ids(), ["123"])

    def test_invalid_allowed_value(self):
        self.assert_error(
            {"Accounts": accounts_sheet(Status="active"), "Bank A": balances_sheet()},
            "Sheet 'Accounts'", "'Status' must be one of Active, Closed", "row(s) 2", "'active'",
        )

    def test_missing_column(self):
        self.assert_error(
            {"Accounts": accounts_sheet().drop(columns="Currency"), "Bank A": balances_sheet()},
            "missing required column(s) 'Currency'",
        )

    def test_duplicate_account_id(self):
        sheet = pd.concat([accounts_sheet(), accounts_sheet()], ignore_index=True)
        self.assert_error(
            {"Accounts": sheet, "Bank A": balances_sheet()},
            "'Account id' must be unique", "'Bank A'", "row(s) 2, 3",
        )

    def test_missing_account_sheet(self):
        self.assert_error({"Accounts": accounts_sheet()}, "has no sheet named 'Bank A'")

    def test_blank_and_non_numeric_balance(self):
        balances = balances_sheet().astype({"Balance": object})
        balances.loc[0, "Balance"] = "abc"
        balances.loc[1, "Balance"] = None
        self.assert_error(
            {"Accounts": accounts_sheet(), "Bank A": balances},
            "Sheet 'Bank A'", "'Balance' must be a number in Excel row(s) 2 (got 'abc')",
            "'Balance' is blank in Excel row(s) 3",
        )

    def test_invalid_date(self):
        balances = balances_sheet()
        balances.loc[1, "Date"] = "not a date"
        self.assert_error(
            {"Accounts": accounts_sheet(), "Bank A": balances},
            "Sheet 'Bank A' has a blank or invalid 'Date' in Excel row(s) 3",
        )

    def test_empty_trailing_rows_are_ignored(self):
        balances = pd.concat([balances_sheet(), pd.DataFrame([{}, {}])], ignore_index=True)
        accounts = create_accounts(self.write({"Accounts": accounts_sheet(), "Bank A": balances}))
        self.assertEqual(len(accounts["Bank A"].transactions), 2)

    def test_invalid_holdings(self):
        self.assert_error(
            {"Holdings": holdings_sheet(Price=-1, ISIN=None)},
            "Sheet 'Holdings'", "'Price' must not be negative", "'ISIN' is blank",
            loader=create_holdings,
        )


class TestClosedAccounts(WorkbookTestCase):
    """An account's balance is zero after it closes instead of carrying forward."""

    def load(self, bank_a: pd.DataFrame):
        # Bank B stays open until 10/01/2025, stretching the date range past
        # Bank A's last entry on 02/01/2025.
        bank_b = bank_a.iloc[[0]].assign(**{"Account id": "Bank B"})
        for column in ("Status", "Closed date"):
            if column in bank_b:
                bank_b[column] = None
        sheets = {
            "Accounts": pd.concat([bank_a, bank_b], ignore_index=True),
            "Bank A": balances_sheet(),
            "Bank B": pd.DataFrame(
                {"Date": ["01/01/2025", "10/01/2025"], "Balance": [5.0, 5.0], "Transaction number": [1, 2]}
            ),
        }
        result = create_accounts(self.write(sheets))
        result.calculate_balances()
        return result

    def test_closed_date_zeroes_balance_after_closing(self):
        accounts = self.load(accounts_sheet(Status=None, **{"Closed date": "05/01/2025"}))
        bank_a = accounts.merged_balances["Bank A"]
        self.assertEqual(accounts["Bank A"].status, "Closed")
        self.assertEqual(bank_a["2025-01-05"], 120.0)
        self.assertEqual(bank_a["2025-01-06"], 0.0)
        self.assertEqual(bank_a["2025-01-10"], 0.0)

    def test_closed_status_without_date_closes_at_last_entry(self):
        accounts = self.load(accounts_sheet(Status="Closed"))
        bank_a = accounts.merged_balances["Bank A"]
        self.assertEqual(accounts["Bank A"].closed_date, pd.Timestamp("2025-01-02"))
        self.assertEqual(bank_a["2025-01-02"], 120.0)
        self.assertEqual(bank_a["2025-01-03"], 0.0)

    def test_open_account_still_carries_forward(self):
        accounts = self.load(accounts_sheet())
        self.assertEqual(accounts["Bank A"].status, "Active")
        self.assertEqual(accounts.merged_balances["Bank A"]["2025-01-10"], 120.0)

    def test_status_column_is_optional(self):
        accounts = self.load(accounts_sheet().drop(columns="Status"))
        self.assertEqual(accounts["Bank A"].status, "Active")

    def test_active_with_closed_date_is_rejected(self):
        self.assert_error(
            {"Accounts": accounts_sheet(**{"Closed date": "05/01/2025"}), "Bank A": balances_sheet()},
            "marked 'Active' that also have a 'Closed date' in Excel row(s) 2",
        )

    def test_entries_after_closed_date_are_rejected(self):
        self.assert_error(
            {"Accounts": accounts_sheet(Status="Closed", **{"Closed date": "01/01/2025"}),
             "Bank A": balances_sheet()},
            "Sheet 'Bank A' has balance entries after the account's closed date 01/01/2025 in Excel row(s) 3",
        )

    def test_invalid_closed_date_is_rejected(self):
        self.assert_error(
            {"Accounts": accounts_sheet(**{"Closed date": "someday"}), "Bank A": balances_sheet()},
            "Sheet 'Accounts' has an invalid 'Closed date' in Excel row(s) 2",
        )


if __name__ == "__main__":
    unittest.main()
