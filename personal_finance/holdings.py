import logging
import os
from dotenv import load_dotenv
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import yfinance as yf

logger = logging.getLogger(__name__)

def _fetch_from_yf(yf_name: str, start_date: datetime, end_date: datetime) -> pd.Series:
    try:
        t = yf.Ticker(yf_name)
        # Add 1 day to end_date to ensure inclusive fetching
        data = t.history(start=start_date, end=end_date + pd.Timedelta(days=1))
        if data.empty:
            return pd.Series(dtype=float)
            
        data.index = data.index.tz_localize(None).normalize()
        series = data["Close"]
        
        currency = t.fast_info.get("currency", "GBP")
        if currency == "GBp":
            series = series / 100
        elif currency and currency != "GBP":
            fx_ticker = f"{currency}GBP=X"
            fx_data = yf.download(fx_ticker, start=start_date, end=end_date + pd.Timedelta(days=1), progress=False)
            if not fx_data.empty:
                fx_series = fx_data["Adj Close"] if "Adj Close" in fx_data.columns else fx_data["Close"]
                if isinstance(fx_series, pd.DataFrame):
                    fx_series = fx_series.iloc[:, 0]
                fx_series.index = fx_series.index.tz_localize(None).normalize()
                fx_series = fx_series.reindex(series.index).ffill().bfill()
                series = series * fx_series
                
        return series
    except Exception as e:
        logger.warning(f"YF fetch failed for {yf_name}: {e}")
        return pd.Series(dtype=float)


def _fetch_from_eodhd(isin: str, start_date: datetime, end_date: datetime) -> pd.Series:
    load_dotenv()
    api_key = os.environ.get("EODHD_API_KEY")
    if not api_key:
        return pd.Series(dtype=float)
        
    try:
        search_url = f"https://eodhd.com/api/search/{isin}?api_token={api_key}&fmt=json"
        search_resp = requests.get(search_url)
        search_resp.raise_for_status()
        search_data = search_resp.json()
        if not search_data:
            return pd.Series(dtype=float)
            
        eod_ticker = search_data[0]["Code"] + "." + search_data[0]["Exchange"]
        currency = search_data[0].get("Currency", "GBP")
        
        eod_url = f"https://eodhd.com/api/eod/{eod_ticker}?from={start_date.strftime('%Y-%m-%d')}&to={end_date.strftime('%Y-%m-%d')}&api_token={api_key}&fmt=json"
        eod_resp = requests.get(eod_url)
        eod_resp.raise_for_status()
        eod_data = eod_resp.json()
        
        if not eod_data:
            return pd.Series(dtype=float)
            
        df = pd.DataFrame(eod_data)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        series = df["adjusted_close"] if "adjusted_close" in df.columns else df["close"]
        
        if currency == "GBX":
            series = series / 100
        elif currency and currency != "GBP":
            fx_ticker = f"{currency}GBP=X"
            fx_data = yf.download(fx_ticker, start=start_date, end=end_date + pd.Timedelta(days=1), progress=False)
            if not fx_data.empty:
                fx_series = fx_data["Adj Close"] if "Adj Close" in fx_data.columns else fx_data["Close"]
                if isinstance(fx_series, pd.DataFrame):
                    fx_series = fx_series.iloc[:, 0]
                fx_series.index = fx_series.index.tz_localize(None).normalize()
                fx_series = fx_series.reindex(series.index).ffill().bfill()
                series = series * fx_series
                
        return series
    except Exception as e:
        logger.warning(f"EODHD fetch failed for ISIN {isin}: {e}")
        return pd.Series(dtype=float)


def _get_required_dates(group: pd.DataFrame, end_date: datetime) -> pd.DatetimeIndex:
    daily_shares = group.groupby("date")["shares"].sum()
    first_date = daily_shares.index.min()
    full_range = pd.date_range(first_date, end_date, freq="D")
    
    cum_shares = daily_shares.reindex(full_range, fill_value=0).cumsum()
    # Epsilon for float comparisons
    required = cum_shares[cum_shares > 1e-6].index
    
    tx_dates = daily_shares[daily_shares != 0].index
    required = required.union(tx_dates)
    
    return required.sort_values()


def _get_contiguous_ranges(dates: pd.DatetimeIndex, max_gap_days: int = 7):
    if len(dates) == 0:
        return []
    
    ranges = []
    start_date = dates[0]
    diffs = dates.to_series().diff()
    
    for i in range(1, len(dates)):
        if diffs.iloc[i].days > max_gap_days:
            end_date = dates[i-1]
            ranges.append((start_date, end_date))
            start_date = dates[i]
            
    ranges.append((start_date, dates[-1]))
    return ranges


def get_historical_holdings(
    table: pd.DataFrame,
    end_date: datetime = None
) -> pd.DataFrame:
    if end_date is None:
        end_date = datetime.now()

    table = table.assign(Date=pd.to_datetime(table["date"]))
    start_date = table["date"].min()
    date_range = pd.date_range(start_date, end_date, freq="D")
    
    table["isin"] = table["isin"].astype(str)
    isin_names = table.groupby("isin")["full_name"].first().to_dict()

    cache_path = "price_cache.csv"
    if os.path.exists(cache_path):
        cache_df = pd.read_csv(cache_path, parse_dates=["date"])
    else:
        cache_df = pd.DataFrame(columns=["date", "isin", "close"])
        
    cache_df["date"] = pd.to_datetime(cache_df["date"])
    price_data_dict = {}
    new_data_list = []
    
    for isin, group in table.groupby("isin"):
        asset_start_date = group["date"].min()
        full_range = pd.date_range(asset_start_date, end_date, freq="D")
        required_dates = _get_required_dates(group, end_date)
        
        merged_series = pd.Series(dtype=float)
        
        if isin in cache_df["isin"].values:
            asset_cache = cache_df[cache_df["isin"] == isin].copy()
            asset_cache.set_index("date", inplace=True)
            merged_series = asset_cache["close"]
            
            # In case cache has duplicates, keep last
            merged_series = merged_series[~merged_series.index.duplicated(keep="last")]
        
        missing_dates = required_dates.difference(merged_series.index)
        
        if not missing_dates.empty:
            yf_names = group["yf_name"].dropna().unique()
            primary_yf_name = yf_names[0] if len(yf_names) > 0 else None
            
            all_fetched = pd.Series(dtype=float)
            
            for block_start, block_end in _get_contiguous_ranges(missing_dates, max_gap_days=7):
                fetched_prices = pd.Series(dtype=float)
                if primary_yf_name:
                    fetched_prices = _fetch_from_yf(primary_yf_name, block_start, block_end)
                    
                if fetched_prices.empty:
                    fetched_prices = _fetch_from_eodhd(isin, block_start, block_end)
                    
                if fetched_prices.empty:
                    logger.warning(f"Could not fetch prices from YF or EODHD for ISIN {isin} between {block_start.date()} and {block_end.date()}.")
                else:
                    all_fetched = pd.concat([all_fetched, fetched_prices])

            if not all_fetched.empty:
                all_fetched = all_fetched[~all_fetched.index.duplicated(keep="last")]
                merged_series = pd.concat([merged_series, all_fetched])
                merged_series = merged_series[~merged_series.index.duplicated(keep="last")]
                
                new_data = all_fetched.reset_index()
                new_data.columns = ["date", "close"]
                new_data["isin"] = isin
                new_data_list.append(new_data)

            unfetched_dates = missing_dates.difference(all_fetched.index) if not all_fetched.empty else missing_dates
            if not unfetched_dates.empty:
                unfetched_data = pd.DataFrame({
                    "date": unfetched_dates,
                    "isin": isin,
                    "close": np.nan
                })
                new_data_list.append(unfetched_data)
                
        # Forward fill over the full possible range. This perfectly carries cache NaNs 
        # as well as bridging any gaps where there was no holding.
        merged_series = merged_series.reindex(full_range).ffill()
        
        # Fallback to cost basis for remaining NaNs
        if merged_series.isna().any():
            cost_series = group.set_index("date")["price"]
            cost_series = cost_series[~cost_series.index.duplicated(keep="last")].reindex(full_range).ffill()
            merged_series = merged_series.fillna(cost_series)
            
        merged_series = merged_series.bfill()
        price_data_dict[isin] = merged_series
        
    price_data = pd.DataFrame(price_data_dict).reindex(date_range).ffill()
    
    if new_data_list:
        new_data_df = pd.concat(new_data_list, ignore_index=True)
        updated_cache = pd.concat([cache_df, new_data_df], ignore_index=True)
        updated_cache.drop_duplicates(subset=["date", "isin"], keep="last", inplace=True)
        updated_cache.sort_values(["isin", "date"]).to_csv(cache_path, index=False)

    # Calculate historical shares per ISIN
    holdings = (
        table.groupby(["isin", "date"])["shares"]
        .sum()
        .groupby(level=0)
        .cumsum()
        .reset_index()
        .pivot(index="date", columns="isin", values="shares")
        .reindex(date_range)
        .ffill()
        .fillna(0)
    )

    output = (
        holdings.mul(price_data)
        .assign(**{
            "balance": lambda x: x.sum(axis=1),
            "transaction_number": np.arange(1, 1+len(holdings))
        })
        .rename(columns=isin_names)
        .rename_axis("date")
        .reset_index()
    )
    output.to_csv("holdings.csv")

    return output

