import unittest
from unittest import mock

import numpy as np
import pandas as pd

from personal_finance.figures import holdings_analysis
from personal_finance.figures.holdings_analysis import (
    plot_covariance_heatmap,
    plot_tickers_evolution,
)

TICKERS = ["AAA.L", "BBB.L"]


def fake_download():
    """A frame shaped like yf.download's output for two tickers."""
    index = pd.date_range("2025-01-01", periods=30, freq="B")
    rng = np.random.default_rng(0)
    close = pd.DataFrame(
        100 + rng.normal(0, 1, (len(index), len(TICKERS))).cumsum(axis=0),
        index=index,
        columns=TICKERS,
    )
    return pd.concat({"Close": close}, axis=1)


class TestHoldingsAnalysis(unittest.TestCase):
    def setUp(self):
        holdings_analysis._PRICE_CACHE.clear()

    def test_failed_download_returns_none(self):
        with mock.patch.object(
            holdings_analysis.yf, "download", return_value=pd.DataFrame()
        ) as download:
            self.assertIsNone(plot_covariance_heatmap(TICKERS))
            self.assertIsNone(plot_tickers_evolution(TICKERS, {}))
        # Failures are not cached, so each chart retries the download.
        self.assertEqual(download.call_count, 2)

    def test_charts_share_one_download(self):
        with mock.patch.object(
            holdings_analysis.yf, "download", return_value=fake_download()
        ) as download:
            self.assertIsNotNone(plot_covariance_heatmap(TICKERS))
            self.assertIsNotNone(plot_tickers_evolution(list(reversed(TICKERS)), {}))
        download.assert_called_once()


if __name__ == "__main__":
    unittest.main()
