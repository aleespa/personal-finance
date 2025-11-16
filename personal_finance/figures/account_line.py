import plotly.graph_objects as go
import pandas as pd

def plot_line_chart_account_plotly(accounts, account_id: str):
    """
    Create an interactive Plotly line chart for a single account.

    Parameters
    ----------
    accounts : AccountList
        Object containing merged_balances (DataFrame with date index)
    account_id : str
        The account to plot

    Returns
    -------
    plotly.graph_objects.Figure
    """
    rolling_avg = accounts.merged_balances.rolling(window=7, min_periods=1).mean()
    df = rolling_avg[[account_id]].fillna(0)

    x = df.index
    y = df[account_id]

    # Split positive and negative
    y_pos = y.clip(lower=0)
    y_neg = y.clip(upper=0)

    fig = go.Figure()

    # Positive area
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y_pos,
            fill='tozeroy',
            mode='lines',
            line=dict(color='green'),
            name='Positive'
        )
    )

    # Negative area
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y_neg,
            fill='tozeroy',
            mode='lines',
            line=dict(color='red'),
            name='Negative'
        )
    )

    # Add zero line
    fig.add_hline(y=0, line_dash='dash', line_color='black', opacity=0.4)

    # Layout
    fig.update_layout(
        title=f"{account_id} - Rolling 7-day Average Balance",
        xaxis_title="Date",
        yaxis_title="Balance (£)",
        template="plotly_white",
        height=500,
    )

    fig.update_yaxes(tickprefix="£")
    fig.update_xaxes(showgrid=True)

    return fig
