import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import streamlit as st

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

if uploaded_file:
    accounts = create_accounts(uploaded_file)
    st.session_state.accounts = accounts
    st.success("Workbook loaded!")

if st.session_state.accounts:
    accounts = st.session_state.accounts
    accounts.calculate_balances()
    st.session_state.year_data = prepare_monthly_diff(accounts)

    if st.session_state.year_data:
        year_data = st.session_state.year_data
        years = sorted(year_data.keys())

        # The selectbox will trigger a rerun of the script
        year = st.selectbox("Select a year", years)

        df = year_data[year]
        fig = plot_monthly_diff_plotly(year, df)

        st.plotly_chart(fig, use_container_width=True)