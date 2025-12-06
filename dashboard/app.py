import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import pandas as pd
import streamlit as st


from personal_finance.figures.monthly_bars import prepare_monthly_diff

from personal_finance.data import create_accounts

from dashboard.fragments import (
    show_monthly_diff,
    show_account_line,
    show_balance_pie,
    show_stacked_barchart,
    show_stacked_barchart,
    show_transactions_fragment,
    show_summary,
)





st.set_page_config(page_title="Finance Dashboard", layout="wide")
st.title("📊 Personal Finance Dashboard")

uploaded_file = st.file_uploader("Upload workbook", type=["xlsx"])

# Initialize session state
if "accounts" not in st.session_state:
    st.session_state.accounts = None

if "year_data" not in st.session_state:
    st.session_state.year_data = None

if uploaded_file:
    accounts = create_accounts(uploaded_file)
    st.session_state.accounts = accounts

if st.session_state.accounts:
    accounts = st.session_state.accounts
    accounts.calculate_balances()
    st.session_state.year_data = prepare_monthly_diff(accounts)

    show_summary(accounts)

    col1, col2, col3 = st.columns(3)
    with col1:
        show_monthly_diff(st.session_state.year_data)

    with col2:
        show_account_line(accounts)

    with col3:
        show_balance_pie(accounts)

    min_date = pd.to_datetime("2020-01-01").date()
    max_date = pd.to_datetime("today").date()

    # Default values as datetime.date
    default_start = min_date
    default_end = max_date

    show_stacked_barchart(accounts, min_date, max_date, default_start, default_end)

    show_transactions_fragment(accounts, min_date, max_date)
