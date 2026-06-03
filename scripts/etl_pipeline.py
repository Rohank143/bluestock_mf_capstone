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

import sys
sys.path.append(os.path.dirname(__file__))
from live_nav_fetch import fetch_nav_data, SCHEMES

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
