import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import streamlit as st
import pandas as pd

from personal_finance.figures import (
    plot_monthly_diff_plotly, prepare_monthly_diff
)
from personal_finance.data import create_accounts

st.set_page_config(page_title="Finance Dashboard", layout="wide")
st.title("📊 Personal Finance Dashboard")

uploaded_file = st.file_uploader("Upload workbook", type=["xlsx"])

# Initialize session state
if "accounts" not in st.session_state:
    st.session_state.accounts = None

if "year_data" not in st.session_state:
    st.session_state.year_data = None

# Upload file
if uploaded_file:
    accounts = create_accounts(uploaded_file)
    st.session_state.accounts = accounts
    st.success("Workbook loaded!")

# If accounts available: show date inputs & button
if st.session_state.accounts:

    accounts = st.session_state.accounts

    min_date = pd.to_datetime("2010-01-01")
    max_date = pd.to_datetime("today")

    start_date = st.date_input("Start date", min_date)
    end_date   = st.date_input("End date", max_date)

    # Button only triggers computation ONCE
    if st.button("Calculate balances"):
        accounts.calculate_balances(str(start_date), str(end_date))
        st.session_state.year_data = prepare_monthly_diff(accounts)
        st.success("Balances calculated!")

    # If we already have computed data → show plots
    if st.session_state.year_data:

        year_data = st.session_state.year_data
        years = sorted(year_data.keys())

        year = st.selectbox("Select a year", years)

        df = year_data[year]
        fig = plot_monthly_diff_plotly(year, df)

        st.plotly_chart(fig, use_container_width=True)
