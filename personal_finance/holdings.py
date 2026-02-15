from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf


def get_historical_holdings(
    table: pd.DataFrame,
    end_date: datetime = datetime.now()
) -> pd.DataFrame:

    table = table.assign(Date=pd.to_datetime(table["date"]))
    start_date = table["date"].min()
    date_range = pd.date_range(start_date, end_date, freq="D")
    tickers = table["yf_name"].unique().tolist()
    ticker_currencies = {t: yf.Ticker(t).fast_info["currency"] for t in tickers}

    # Download and prepare price data
    price_data = (
        yf.download(tickers, start=start_date, end=end_date, progress=False)
        .pipe(lambda x: x["Adj Close"] if "Adj Close" in x.columns else x["Close"])
        .pipe(lambda x: x.to_frame(name=tickers[0]) if isinstance(x, pd.Series) else x)
    )

    # Convert to GBP if necessary
    unique_currencies = {ticker_currencies.get(t) for t in tickers}
    fx_rates_cache = {}

    for currency in unique_currencies:
        if currency and currency != "GBP" and currency != "GBp":
            fx_ticker = f"{currency}GBP=X"
            fx_data = yf.download(fx_ticker, start=start_date, end=end_date, progress=False)
            if not fx_data.empty:
                fx_series = (
                    fx_data["Adj Close"] if "Adj Close" in fx_data.columns else fx_data["Close"]
                )
                if isinstance(fx_series, pd.DataFrame):
                    fx_series = fx_series.iloc[:, 0]
                fx_rates_cache[currency] = fx_series.reindex(price_data.index).ffill().bfill()

    for t in tickers:
        currency = ticker_currencies.get(t)
        if currency == "GBp":
            price_data[t] = price_data[t] / 100
        elif currency in fx_rates_cache:
            price_data[t] = price_data[t] * fx_rates_cache[currency]

    price_data = (
        price_data
        .reindex(date_range)
        .ffill()
    )

    # Calculate historical shares per ticker using chained operations
    holdings = (
        table.groupby(["yf_name", "date"])["shares"]
        .sum()
        .groupby(level=0)
        .cumsum()
        .reset_index()
        .pivot(index="date", columns="yf_name", values="shares")
        .reindex(date_range)
        .ffill()
        .fillna(0)
    )

    return (
        holdings.mul(price_data)
        .assign(**{
            "Balance": lambda x: x.sum(axis=1),
            "Transaction number": np.arange(1, 1+len(holdings))
        })
        .rename_axis("date")
        .reset_index()
    )

