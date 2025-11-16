# Personal Finance Dashboard

A Streamlit-based web dashboard to visualize and analyze personal finance data. Users can upload Excel workbooks containing account and transaction data, calculate balances, and explore interactive charts of monthly balances and differences.

## Features

* Upload Excel workbook with accounts and transactions
* Calculate balances for a selected date range
* Interactive Plotly charts:

  * Monthly balance differences per year
  * Individual account balances
  * Monthly stacked balances by bank
* Supports multiple currencies (GBP, MXN)
* Easy-to-extend modular code

## Installation

### 1. Clone the repository

```bash
git clone <repository_url>
cd personal-finance
```

### 2. Create a virtual environment using uv

```bash
uv create .venv
```

Activate the environment:

* Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

* macOS / Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
uv install -r requirements.txt
```

---

## Data Format

The dashboard expects an **Excel workbook** with at least two sheets:

### 1. `accounts` sheet

| account_id | bank      | account_number | type    | currency | status |
| ---------- | --------- | -------------- | ------- | -------- | ------ |
| A1         | HSBC      | 12345678       | Current | GBP      | Active |
| A2         | Santander | 98765432       | Savings | GBP      | Active |

* `type` must be one of: `Current`, `Savings`, `Credit Card`, `Loan`, `Investment`
* `currency` must be `GBP` or `MXN`
* `status` must be `Active` or `Closed`

### 2. `transactions` sheet

| date       | transaction_number | balance |
 | ---------- | ------------------ | ------- |
| 2025-01-01 | 1                  | 1000    |
| 2025-01-02 | 2                  | 1200    |
| 2025-01-01 | 1                  | 5000    |

* `date` should be in a format readable by `pandas.to_datetime`
* `balance` is the end-of-day account balance

---

## Running the Dashboard

From the project root:

```bash
streamlit run dashboard/app.py
```

* Open the URL provided by Streamlit (usually `http://localhost:8501`)
* Upload your workbook
* Select start and end dates
* Click **Calculate balances**
* Explore interactive charts by selecting a year

---

## Notes

* Ensure your Excel workbook follows the required column names and types.
* Large workbooks may take some time to compute balances; caching can be added for performance.
* All charts are interactive using Plotly.
