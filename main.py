import re
from pathlib import Path

import pandas as pd

from personal_finance import holdings
from personal_finance.data import normalize_column_names


def main():
    table = (pd.read_excel(r"data\demo_data.xlsx", sheet_name="Holdings")
                .pipe(normalize_column_names))
    r = holdings.get_historical_holdings(table)
    r.to_clipboard(excel=True)



if __name__ == "__main__":
    main()
