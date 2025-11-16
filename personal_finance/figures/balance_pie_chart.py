import pandas as pd
import plotly.graph_objects as go


def plot_account_balance_pie(accounts, selected_date):
    """
    Plot a pie chart of account balances for a specific date (month-end).

    Only accounts with positive balances are included.
    """
    # Resample to month-end
    mb = accounts.merged_balances
    monthly = mb[[col for col in mb.columns if col != "total"]].resample("ME").last()

    # Ensure selected_date is Timestamp
    selected_date = pd.to_datetime(selected_date)

    # Pick the closest month-end date <= selected_date
    possible_dates = monthly.index[monthly.index <= selected_date]
    if len(possible_dates) == 0:
        raise ValueError("No available month-end data before the selected date.")
    date = possible_dates[-1]  # last date before or equal to selected_date

    # Extract balances for that date
    balances = monthly.loc[date]

    # Filter only positive balances
    positive_balances = balances[balances > 0]

    # Create pie chart
    fig = go.Figure(
        go.Pie(
            labels=positive_balances.index,
            values=positive_balances.values,
            textinfo='label+percent',
            hovertemplate="%{label}<br>Balance: £%{value:,.2f}<extra></extra>"
        )
    )

    fig.update_layout(
        title=f"Account Balance Distribution — {date.strftime('%b %Y')}",
        template="plotly_white",
        height=500
    )

    return fig