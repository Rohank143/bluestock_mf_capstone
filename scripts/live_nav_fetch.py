import pandas as pd
import requests
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / 'data' / 'raw'

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

if __name__ == "__main__":
    logging.info("Starting standalone Live NAV Fetching...")
    for name, code in SCHEMES.items():
        fetch_nav_data(code, name)
    logging.info("Live NAV Fetching completed.")
