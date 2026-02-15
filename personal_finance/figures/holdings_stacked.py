import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def plot_holdings_stacked(accounts, start_date, end_date):
    """
    Plots the daily evolution of Holdings account stacked by ticker.
    """
    if "Holdings" not in accounts.get_ids():
        return None

    holdings_acc = accounts["Holdings"]
    df = holdings_acc.historical_data.copy()
    
    # Ensure date is index
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    
    # Filter by date range
    df = df.loc[start_date:end_date]

    # Exclude non-ticker columns
    cols_to_exclude = ["balance", "transaction_number"]
    ticker_cols = [c for c in df.columns if c not in cols_to_exclude]

    fig = go.Figure()

    for ticker in ticker_cols:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[ticker],
                mode='lines',
                line=dict(width=0.5),
                stackgroup='one',
                name=ticker
            )
        )

    fig.update_layout(
        title="Holdings Daily Evolution by Ticker",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Value (£)", tickprefix="£"),
        template="plotly_white",
        height=600,
        legend=dict(title="Ticker", x=1.05, y=1),
    )

    return fig
