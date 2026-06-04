import pandas as pd
import glob
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent.parent
    raw_dir = base_dir / 'data' / 'raw'

    print("=== Task 3: Load 10 CSV datasets and print shape, dtypes, head ===")
    csv_files = sorted(raw_dir.glob("[0-1][0-9]_*.csv"))
    
    datasets = {}
    
    for file_path in csv_files:
        df = pd.read_csv(file_path)
        datasets[file_path.name] = df
        print(f"\n--- {file_path.name} ---")
        print(f"Shape: {df.shape}")
        print("Dtypes:")
        print(df.dtypes)
        print("Head:")
        print(df.head(3))
        # Anomalies check can be brief: missing values, incorrect types (e.g., dates as objects)
        print("Missing Values:")
        print(df.isnull().sum())
    
    print("\n=== Task 6: Explore Fund Master ===")
    fund_master = datasets.get('01_fund_master.csv')
    if fund_master is not None:
        print("Unique Fund Houses:", fund_master['fund_house'].nunique(), "->", fund_master['fund_house'].unique()[:5])
        print("Categories:", fund_master['category'].unique())
        print("Sub-categories:", fund_master['sub_category'].unique())
        if 'risk_category' in fund_master.columns:
            print("Risk Grades:", fund_master['risk_category'].unique())
        elif 'risk_grade' in fund_master.columns:
            print("Risk Grades:", fund_master['risk_grade'].unique())
        
        # AMFI scheme code structure
        print("AMFI Scheme Codes type:", fund_master['amfi_code'].dtype)
        print("Sample AMFI Codes:", fund_master['amfi_code'].head().tolist())
    
    print("\n=== Task 7: Validate AMFI codes ===")
    nav_history = datasets.get('02_nav_history.csv')
    if fund_master is not None and nav_history is not None:
        master_codes = set(fund_master['amfi_code'].unique())
        nav_codes = set(nav_history['amfi_code'].unique()) if 'amfi_code' in nav_history.columns else set(nav_history['scheme_code'].unique()) if 'scheme_code' in nav_history.columns else set()
        
        missing_in_nav = master_codes - nav_codes
        print(f"Total schemes in master: {len(master_codes)}")
        print(f"Total schemes in NAV history: {len(nav_codes)}")
        print(f"Schemes in master but missing in NAV history: {len(missing_in_nav)}")
        
        print("\nData Quality Summary:")
        if len(missing_in_nav) == 0:
            print("- All AMFI codes in fund_master exist in nav_history.")
        else:
            print(f"- {len(missing_in_nav)} AMFI codes from fund_master are missing in nav_history.")
        
        print("- Check dates in NAV history, they might be loaded as strings (object) and need conversion to datetime.")

if __name__ == '__main__':
    main()
