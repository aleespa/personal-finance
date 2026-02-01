import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def plot_stacked_ts_balance_by_bank(accounts, start_date, end_date):
    """
    Interactive Plotly version of the diverging stacked monthly balance chart.
    Positive balances stack upward, negative downward. Colored by bank.

    Parameters
    ----------
    accounts : AccountList
        The AccountList object with merged_balances
    start_date, end_date : str or pd.Timestamp
        Date range for the chart

    Returns
    -------
    fig : plotly.graph_objects.Figure
    """
    # Copy relevant data
    df = accounts.merged_balances.copy().loc[start_date:end_date]

    # Exclude total column
    if "total" in df.columns:
        df = df.drop(columns="total")

    # Month-end resampling
    monthly = df.resample("ME").last()

    # Map account_id → bank
    account_to_bank = {acc.account_id: acc.bank for acc in accounts.accounts}

    # Assign colors per bank
    unique_banks = list({acc.bank for acc in accounts.accounts if acc.bank})
    cmap = px.colors.qualitative.Plotly
    bank_colors = {bank: cmap[i % len(cmap)] for i, bank in enumerate(unique_banks)}
    account_colors = {
        acc.account_id: bank_colors.get(acc.bank, "gray") for acc in accounts.accounts
    }

    # Initialize figure
    fig = go.Figure()

    bottom_pos = pd.Series(0, index=monthly.index)
    bottom_neg = pd.Series(0, index=monthly.index)

    for col in monthly.columns:
        values = monthly[col].fillna(0)
        color = account_colors.get(col, "gray")

        pos_values = values.clip(lower=0)
        neg_values = values.clip(upper=0)

        # Positive stack
        fig.add_trace(
            go.Bar(
                x=monthly.index,
                y=pos_values,
                base=bottom_pos,
                name=f"{col} ({account_to_bank.get(col,'Unknown')})",
                marker_color=color,
            )
        )
        bottom_pos += pos_values

        # Negative stack
        fig.add_trace(
            go.Bar(
                x=monthly.index,
                y=neg_values,
                base=bottom_neg,
                marker_color=color,
                showlegend=False,  # hide duplicate legend entries
            )
        )
        bottom_neg += neg_values

    # Layout
    fig.update_layout(
        title="Monthly Balances by Account (Positive/Negative Stacked by Bank)",
        barmode="relative",  # diverging stacked bars
        xaxis=dict(title="Month", tickformat="%b\n%Y"),
        yaxis=dict(title="Balance (£)", tickprefix="£"),
        template="plotly_white",
        height=600,
        legend=dict(title="Account (Bank)", x=1.05, y=1),
    )

    return fig
