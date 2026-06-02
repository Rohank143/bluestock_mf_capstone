import os
import glob
import pandas as pd
import requests
import sqlite3
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / 'data' / 'raw'
PROCESSED_DIR = BASE_DIR / 'data' / 'processed'
DB_PATH = BASE_DIR / 'data' / 'db' / 'bluestock_mf.db'

# Schemes to fetch
SCHEMES = {
    'HDFC_Top_100_Direct': 125497,
    'SBI_Bluechip': 119551,
    'ICICI_Bluechip': 120503,
    'Nippon_Large_Cap': 118632,
    'Axis_Bluechip': 119092,
    'Kotak_Bluechip': 120841
}

def fetch_nav_data(scheme_code, scheme_name):
    """Fetches live NAV from mfapi.in and saves to a raw CSV."""
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and data['data']:
            df = pd.DataFrame(data['data'])
            # Clean and standardise columns
            df.rename(columns={'date': 'Date', 'nav': 'NAV'}, inplace=True)
            df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
            df['NAV'] = pd.to_numeric(df['NAV'])
            
            # Add scheme metadata
            df['scheme_code'] = scheme_code
            df['scheme_name'] = scheme_name
            
            # Sort by date ascending
            df.sort_values('Date', inplace=True)
            
            raw_csv_path = RAW_DIR / f"{scheme_name}_{scheme_code}_raw.csv"
            df.to_csv(raw_csv_path, index=False)
            logging.info(f"Successfully fetched and saved raw data for {scheme_name} to {raw_csv_path}")
            return df
        else:
            logging.warning(f"No data found for scheme {scheme_name} ({scheme_code})")
            return None
    except Exception as e:
        logging.error(f"Error fetching data for {scheme_name} ({scheme_code}): {e}")
        return None

def process_and_load_csvs():
    """Loads all raw CSV datasets, prints basic stats, and loads to SQLite."""
    csv_files = glob.glob(str(RAW_DIR / '*.csv'))
    
    if not csv_files:
        logging.warning("No CSV files found in data/raw/")
        return

    engine = sqlite3.connect(DB_PATH)
    
    for file in csv_files:
        file_name = os.path.basename(file)
        # Strip leading numbers and underscores for cleaner table names (e.g. 01_fund_master -> fund_master)
        table_name = os.path.splitext(file_name)[0]
        import re
        table_name = re.sub(r'^\d+_', '', table_name)
        try:
            df = pd.read_csv(file)
            logging.info(f"\n{'='*40}\nDataset: {file_name}\n{'='*40}")
            logging.info(f"Shape: {df.shape}")
            logging.info(f"Data Types:\n{df.dtypes}")
            logging.info(f"Head:\n{df.head(3)}")
            
            # Load to DB
            df.to_sql(table_name, con=engine, if_exists='replace', index=False)
            logging.info(f"Successfully loaded {file_name} into SQLite table '{table_name}'")
        except Exception as e:
            logging.error(f"Error processing {file_name}: {e}")
            
    engine.close()

def main():
    logging.info("Starting ETL Pipeline")
    
    # 1. Fetch NAV data from API
    for name, code in SCHEMES.items():
        fetch_nav_data(code, name)
        
    # 2. Process all raw CSVs and load into DB
    process_and_load_csvs()
    
    logging.info("ETL Pipeline completed successfully")

if __name__ == "__main__":
    main()
