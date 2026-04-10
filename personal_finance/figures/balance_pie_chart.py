import colorsys
import json
import os
import pandas as pd
import plotly.graph_objects as go

def _hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HSL (0-1 range) to hex color string."""
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

def _hex_to_hsl(hex_str: str) -> tuple:
    """Convert hex color string to HSL (0-1 range)."""
    hex_str = hex_str.lstrip('#')
    r, g, b = tuple(int(hex_str[i:i+2], 16)/255.0 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (h, s, l)

def _generate_bank_palette(banks: list) -> dict:
    """Assign colors to banks, using bank_colors.json as override."""
    palette = {}
    
    config_path = "bank_colors.json"
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except Exception:
            pass

    golden_ratio = 0.618033988749895
    hue = 0.0
    
    # Sort banks to keep order consistent
    for bank in sorted(banks):
        if bank in config:
            palette[bank] = _hex_to_hsl(config[bank])
        else:
            palette[bank] = (hue % 1.0, 0.70, 0.45)
            hue += golden_ratio
            
    return palette

def plot_account_balance_pie(accounts, selected_date):
    """
    Plot a treemap chart of account balances for a specific date (month-end),
    grouped by Bank -> Account, with per-bank color families.
    Holdings are subdivided by ticker and colored green/red.
    """
    mb = accounts.merged_balances
    monthly = mb[[col for col in mb.columns if col != "total"]].resample("ME").last()
    selected_date = pd.to_datetime(selected_date)

    possible_dates = monthly.index[monthly.index <= selected_date]
    if len(possible_dates) == 0:
        raise ValueError("No available month-end data before the selected date.")
    date = possible_dates[-1]

    balances = monthly.loc[date]
    positive_balances = balances[balances > 0]

    # Map accounts to banks
    bank_map = {}
    unique_banks = set()
    for acc_id in positive_balances.index:
        if acc_id == "Holdings":
            continue
        acc = accounts[acc_id]
        bank = acc.bank if acc.bank else "Other"
        bank_map[acc_id] = bank
        unique_banks.add(bank)

    bank_hsl = _generate_bank_palette(list(unique_banks))

    ids = []
    labels = []
    parents = []
    values = []
    colors = []

    # 1. Regular Banks and Accounts
    for bank in sorted(list(unique_banks)):
        acc_ids = [aid for aid, b in bank_map.items() if b == bank]
        bank_total = sum(positive_balances[aid] for aid in acc_ids)
        
        ids.append(bank)
        labels.append(bank)
        parents.append("")
        values.append(bank_total)
        colors.append(_hsl_to_hex(*bank_hsl[bank]))

        hsl = bank_hsl[bank]
        for idx, aid in enumerate(sorted(acc_ids)):
            ids.append(f"{bank}_{aid}")
            labels.append(aid)
            parents.append(bank)
            values.append(positive_balances[aid])
            
            # For variations, we slightly vary the lightness around the primary color
            step = 0.30 / (len(acc_ids) - 1) if len(acc_ids) > 1 else 0
            l_var = max(0.25, min(0.75, hsl[2] - 0.15 + (idx * step)))
            colors.append(_hsl_to_hex(hsl[0], hsl[1], l_var))

    # 2. Holdings
    if "Holdings" in positive_balances.index:
        holdings_acc = accounts["Holdings"]
        
        tx_df = holdings_acc.transactions
        past_tx = tx_df[pd.to_datetime(tx_df['date']).dt.date <= date.date()]
        
        holdings_sub_ids = []
        holdings_sub_labels = []
        holdings_sub_parents = []
        holdings_sub_values = []
        holdings_sub_colors = []

        if not past_tx.empty:
            latest = past_tx.iloc[-1]
            cols_to_exclude = {"date", "balance", "transaction_number", "valuation"}
            tickers = [c for c in tx_df.columns if c not in cols_to_exclude 
                      and not c.endswith("_valuation") and not c.endswith("_invested")]
            
            for ticker in sorted(tickers):
                inv_val = latest.get(f"{ticker}_invested", 0)
                pnl = latest.get(ticker, 0)
                if inv_val > 0:
                    holdings_sub_ids.append(f"Holdings_{ticker}")
                    holdings_sub_labels.append(ticker)
                    holdings_sub_parents.append("Holdings")
                    holdings_sub_values.append(inv_val)
                    holdings_sub_colors.append('#2ca02c' if pnl >= 0 else '#d62728')

        # Use the sum of added tickers for consistency
        current_holdings_sum = sum(holdings_sub_values)
        if current_holdings_sum > 0:
            ids.append("Holdings")
            labels.append("Holdings")
            parents.append("")
            values.append(current_holdings_sum)
            colors.append("#555555")
            
            ids.extend(holdings_sub_ids)
            labels.extend(holdings_sub_labels)
            parents.extend(holdings_sub_parents)
            values.extend(holdings_sub_values)
            colors.extend(holdings_sub_colors)

    fig = go.Figure(go.Treemap(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(colors=colors, line=dict(width=0.5)),
        texttemplate="<b>%{label}</b><br>£%{value:,.2f}",
        hovertemplate="<b>%{label}</b><br>Balance: £%{value:,.2f}<extra></extra>",
        textfont=dict(size=14),
    ))

    fig.update_layout(
        title=f"Account Balance Distribution — {date.strftime('%b %Y')}",
        template="plotly_white",
        height=500,
        margin=dict(t=50, l=10, r=10, b=10)
    )

    return fig