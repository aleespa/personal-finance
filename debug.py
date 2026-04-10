import argparse
from pathlib import Path

from personal_finance.data import create_accounts, create_holdings

def main():
    parser = argparse.ArgumentParser(description="Debug personal finance data extraction.")
    parser.add_argument("--workbook", type=str, default="data/demo_data.xlsx", help="Path to the excel workbook")
    
    args = parser.parse_args()
    workbook_path = Path(args.workbook)
    
    if not workbook_path.exists():
        print(f"Error: Workbook '{workbook_path}' not found.")
        return
        
    print(f"Loading data from: {workbook_path}")
    
    # Debug Holdings data creation
    print("\n--- Testing create_holdings ---")
    holdings_df = create_holdings(workbook_path)
    if holdings_df is not None:
        print(f"Holdings read successfully: {len(holdings_df)} rows")
        print("First few rows:")
        print(holdings_df.head(3))
    else:
        print("No Holdings data found.")
        
    # Debug Accounts creation (this will calculate historical holdings)
    print("\n--- Testing create_accounts ---")
    accounts = create_accounts(workbook_path)
    print(f"Loaded {len(accounts)} accounts: {accounts.get_ids()}")
    
    if "Holdings" in accounts:
        print("\n--- Holdings Account Debug ---")
        holdings_acc = accounts["Holdings"]
        tx_cols = holdings_acc.transactions.columns.tolist()
        print("Transactions columns:", tx_cols)
        print("Recent transactions summary:")
        print(holdings_acc.transactions[["date", "balance", "valuation"]].tail(5))
        
    print("\n--- Testing calculate_balances ---")
    accounts.calculate_balances()
    print("Merged balances calculated.")
    print("Merged shape:", accounts.merged_balances.shape)
    print("Recent totals:")
    print(accounts.merged_balances.tail(3))
    
    print("\nDebug complete.")

if __name__ == '__main__':
    main()
