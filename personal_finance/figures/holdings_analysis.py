import numpy as np
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def get_last_year_returns(tickers):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    data = yf.download(tickers, start=start_date, end=end_date, progress=False)
    if data.empty:
        return pd.DataFrame()
    
    # Use Adj Close or Close
    prices = data["Adj Close"] if "Adj Close" in data.columns else data["Close"]
    
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])
        
    returns = np.log(prices).diff().dropna()
    return returns, prices

def plot_covariance_heatmap(tickers):
    returns, _ = get_last_year_returns(tickers)
    if returns.empty:
        return None
        
    corr_matrix = returns.corr()
    variances = returns.var() * 252

    # Create the matrix: correlations off-diagonal, annualized variance on diagonal
    final_matrix = corr_matrix.copy()
    for ticker in tickers:
        if ticker in final_matrix.index:
            final_matrix.loc[ticker, ticker] = np.sqrt(variances[ticker])

    final_matrix *= 100

    fig = px.imshow(
        final_matrix,
        labels=dict(x="Ticker", y="Ticker", color="Value"),
        x=final_matrix.columns,
        y=final_matrix.index,
        color_continuous_scale="RdBu_r",
        title="Ticker Analysis: Annualized Variance (Diag) & Correlation (Off-Diag)"
    )
    fig.update_layout(height=500)
    return fig

def plot_tickers_evolution(tickers, names_dict):
    _, prices = get_last_year_returns(tickers)
    if prices.empty:
        return None
    
    # Normalize to start at 100 for comparison.
    # We find the first valid (non-NaN and non-zero) price for each column to normalize.
    def normalize_series(s):
        first_valid_idx = s.first_valid_index()
        if first_valid_idx is None:
            return s
        
        # Find first non-zero value starting from first_valid_idx
        valid_prices = s.loc[first_valid_idx:]
        non_zero_prices = valid_prices[valid_prices != 0]
        
        if non_zero_prices.empty:
            return s
            
        base_price = non_zero_prices.iloc[0]
        return (s / base_price) * 100

    normalized_prices = prices.apply(normalize_series)
    
    fig = go.Figure()
    for ticker in tickers:
        if ticker not in normalized_prices.columns:
            continue
        display_name = names_dict.get(ticker, ticker)
        fig.add_trace(go.Scatter(
            x=normalized_prices.index,
            y=normalized_prices[ticker],
            mode='lines',
            name=display_name
        ))
        
    fig.update_layout(
        title="Ticker Evolution (Normalized, Last Year)",
        xaxis_title="Date",
        yaxis_title="Normalized Price (Start = 100)",
        height=500,
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        )
    )
    return fig
