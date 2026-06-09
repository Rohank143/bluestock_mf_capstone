import pandas as pd
import os

data_dir = r"d:\python\bluestock_mf_capstone\data\processed"

files_to_check = [
    "fund_master.csv",
    "nav_history.csv",
    "investor_transactions.csv",
    "portfolio_holdings.csv"
]

for file in files_to_check:
    path = os.path.join(data_dir, file)
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"--- {file} ---")
        print(df.info())
        print(df.head(3))
        print("\n")
    else:
        print(f"File not found: {file}")
