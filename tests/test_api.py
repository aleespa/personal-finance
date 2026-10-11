import io
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from personal_finance.api.main import create_app
from personal_finance.figures import holdings_analysis

DEMO = Path("data/demo_data.xlsx")


def workbook_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
    return buffer.getvalue()


def simple_sheets() -> dict[str, pd.DataFrame]:
    """One current account and no Holdings sheet."""
    return {
        "Accounts": pd.DataFrame(
            [{"Account id": "Bank A", "Bank": "Barclays", "Type": "Current", "Currency": "GBP"}]
        ),
        "Bank A": pd.DataFrame(
            {
                "Date": ["01/01/2025", "01/02/2025", "01/03/2025"],
                "Balance": [100.0, 150.0, 120.0],
                "Transaction number": [1, 2, 3],
            }
        ),
    }


def upload(client: TestClient, content: bytes, name: str = "book.xlsx"):
    return client.post("/api/workbooks", files={"file": (name, content)})


def fake_download(tickers):
    index = pd.date_range("2025-01-01", periods=30, freq="B")
    rng = np.random.default_rng(0)
    close = pd.DataFrame(
        100 + rng.normal(0, 1, (len(index), len(tickers))).cumsum(axis=0),
        index=index,
        columns=tickers,
    )
    return pd.concat({"Close": close}, axis=1)


class DemoWorkbookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(create_app(frontend_dir=None))
        response = upload(cls.client, DEMO.read_bytes())
        assert response.status_code == 201, response.text
        cls.meta = response.json()
        cls.base = f"/api/workbooks/{cls.meta['id']}"

    def setUp(self):
        holdings_analysis._PRICE_CACHE.clear()

    def test_upload_metadata(self):
        self.assertTrue(self.meta["has_holdings"])
        ids = {a["id"] for a in self.meta["accounts"]}
        self.assertIn("Holdings", ids)
        self.assertIn("Barclays", ids)
        self.assertEqual(self.meta["years"], sorted(self.meta["years"], reverse=True))
        self.assertLessEqual(self.meta["date_min"], self.meta["date_max"])
        self.assertGreater(len(self.meta["months"]), 0)

    def test_summary(self):
        response = self.client.get(f"{self.base}/summary")
        self.assertEqual(response.status_code, 200)
        summary = response.json()
        self.assertEqual(
            summary["active_accounts"] + summary["closed_accounts"], len(self.meta["accounts"])
        )
        self.assertIsNotNone(summary["unrealized_gains"])

    def test_balances_default_to_active_accounts(self):
        table = self.client.get(f"{self.base}/balances").json()
        active = [a["id"] for a in self.meta["accounts"] if a["status"] == "Active"]
        self.assertEqual(table["columns"], ["date"] + active)
        dates = [row["date"] for row in table["rows"]]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_balances_filtered(self):
        response = self.client.get(
            f"{self.base}/balances",
            params={"start": "2025-01-01", "end": "2025-01-31", "accounts": ["Barclays"]},
        )
        table = response.json()
        self.assertEqual(table["columns"], ["date", "Barclays"])
        self.assertEqual(len(table["rows"]), 31)
        self.assertEqual(table["rows"][0]["date"], "2025-01-31")

    def test_balances_unknown_account(self):
        response = self.client.get(f"{self.base}/balances", params={"accounts": ["Nope"]})
        self.assertEqual(response.status_code, 422)

    def assert_figure(self, path, **params):
        response = self.client.get(f"{self.base}/charts/{path}", params=params)
        self.assertEqual(response.status_code, 200, response.text)
        figure = response.json()
        self.assertIn("data", figure)
        self.assertIn("layout", figure)
        self.assertNotIn("plotly_white", response.text)
        return figure

    def test_charts(self):
        year = self.meta["years"][0]
        month = self.meta["months"][0]
        self.assert_figure("monthly-diff", year=year)
        self.assert_figure("account-line")
        self.assert_figure("account-line", account="Barclays")
        self.assert_figure("balance-treemap")
        self.assert_figure("balance-treemap", month=month)
        self.assert_figure("balances-by-bank")
        self.assert_figure("holdings-pnl")

    def test_analysis_charts(self):
        with mock.patch.object(
            holdings_analysis.yf, "download", side_effect=lambda t, **_: fake_download(t)
        ):
            self.assert_figure("holdings-correlation")
            self.assert_figure("holdings-evolution")

    def test_analysis_charts_without_prices(self):
        with mock.patch.object(holdings_analysis.yf, "download", return_value=pd.DataFrame()):
            response = self.client.get(f"{self.base}/charts/holdings-correlation")
        self.assertEqual(response.status_code, 503)

    def test_chart_bad_params(self):
        for path, params in [
            ("monthly-diff", {"year": 1900}),
            ("account-line", {"account": "Nope"}),
            ("balance-treemap", {"month": "1900-01-31"}),
        ]:
            with self.subTest(path=path):
                response = self.client.get(f"{self.base}/charts/{path}", params=params)
                self.assertEqual(response.status_code, 422)


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(frontend_dir=None))

    def test_validation_error(self):
        sheets = simple_sheets()
        del sheets["Bank A"]
        response = upload(self.client, workbook_bytes(sheets))
        self.assertEqual(response.status_code, 422)
        self.assertIn("has no sheet named 'Bank A'", response.json()["detail"])

    def test_not_a_workbook(self):
        response = upload(self.client, b"date,balance\n", name="book.csv")
        self.assertEqual(response.status_code, 422)
        self.assertIn("Excel workbook", response.json()["detail"])

    def test_without_holdings(self):
        response = upload(self.client, workbook_bytes(simple_sheets()))
        self.assertEqual(response.status_code, 201)
        meta = response.json()
        self.assertFalse(meta["has_holdings"])
        base = f"/api/workbooks/{meta['id']}"
        self.assertIsNone(self.client.get(f"{base}/summary").json()["unrealized_gains"])
        for chart in ["holdings-pnl", "holdings-correlation", "holdings-evolution"]:
            with self.subTest(chart=chart):
                self.assertEqual(self.client.get(f"{base}/charts/{chart}").status_code, 409)

    def test_new_upload_replaces_old(self):
        first = upload(self.client, workbook_bytes(simple_sheets())).json()["id"]
        second = upload(self.client, workbook_bytes(simple_sheets())).json()["id"]
        self.assertEqual(self.client.get(f"/api/workbooks/{first}/summary").status_code, 404)
        self.assertEqual(self.client.get(f"/api/workbooks/{second}/summary").status_code, 200)

    def test_unknown_workbook(self):
        response = self.client.get("/api/workbooks/does-not-exist/charts/account-line")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
