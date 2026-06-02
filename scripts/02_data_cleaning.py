import pandas as pd
from sqlalchemy import create_engine, text
import numpy as np
import logging
from pathlib import Path
import glob
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / 'data' / 'raw'
PROCESSED_DIR = BASE_DIR / 'data' / 'processed'
DB_PATH = BASE_DIR / 'data' / 'db' / 'bluestock_mf.db'
SCHEMA_PATH = BASE_DIR / 'sql' / 'schema.sql'

def setup_db(engine):
    """Executes schema.sql to setup the database tables."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = f.read()
    with engine.connect() as conn:
        for statement in schema.split(';'):
            if statement.strip():
                conn.execute(text(statement))
        conn.commit()
    logging.info("Initialized Star Schema in bluestock_mf.db")

def generate_dim_date(start_date, end_date):
    """Generates the dim_date calendar table."""
    date_range = pd.date_range(start=start_date, end=end_date)
    df = pd.DataFrame({'date': date_range})
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['quarter'] = df['date'].dt.quarter
    df['day_of_week'] = df['date'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6])
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    return df

def clean_nav_history():
    logging.info("Cleaning nav_history...")
    file_path = RAW_DIR / '02_nav_history.csv'
    if not file_path.exists():
        logging.warning("nav_history.csv not found.")
        return None
    
    df = pd.read_csv(file_path)
    df.drop_duplicates(inplace=True)
    
    # Parse dates
    df['date'] = pd.to_datetime(df['date'], format='mixed', dayfirst=True)
    
    # Validate NAV > 0
    df = df[df['nav'] > 0]
    
    # Sort and ffill missing dates per fund
    df.set_index('date', inplace=True)
    
    # Create full date range per amfi_code
    cleaned_dfs = []
    for code, group in df.groupby('amfi_code'):
        group = group[~group.index.duplicated(keep='first')]
        # Reindex to full date range
        full_range = pd.date_range(start=group.index.min(), end=group.index.max(), freq='D')
        group_reindexed = group.reindex(full_range)
        group_reindexed['amfi_code'] = code
        # ffill for weekends and holidays
        group_reindexed['nav'] = group_reindexed['nav'].ffill()
        cleaned_dfs.append(group_reindexed)
        
    final_df = pd.concat(cleaned_dfs).reset_index().rename(columns={'index': 'date'})
    final_df['date'] = final_df['date'].dt.strftime('%Y-%m-%d')
    
    # Save
    out_path = PROCESSED_DIR / 'nav_history.csv'
    final_df.to_csv(out_path, index=False)
    logging.info(f"nav_history cleaned: {final_df.shape}")
    return final_df

def clean_investor_transactions():
    logging.info("Cleaning investor_transactions...")
    file_path = RAW_DIR / '08_investor_transactions.csv'
    if not file_path.exists():
        return None
        
    df = pd.read_csv(file_path)
    
    # Parse dates
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], format='mixed').dt.strftime('%Y-%m-%d')
    
    # Standardize transaction_type
    df['transaction_type'] = df['transaction_type'].str.upper().str.strip()
    valid_types = ['SIP', 'LUMPSUM', 'REDEMPTION']
    df.loc[~df['transaction_type'].isin(valid_types), 'transaction_type'] = 'OTHER'
    
    # Validate amount > 0
    df = df[df['amount_inr'] > 0]
    
    # Check KYC
    df['kyc_status'] = df['kyc_status'].str.upper()
    
    out_path = PROCESSED_DIR / 'investor_transactions.csv'
    df.to_csv(out_path, index=False)
    logging.info(f"investor_transactions cleaned: {df.shape}")
    return df

def clean_scheme_performance():
    logging.info("Cleaning scheme_performance...")
    file_path = RAW_DIR / '07_scheme_performance.csv'
    if not file_path.exists():
        return None
        
    df = pd.read_csv(file_path)
    
    # Force returns to numeric, coerce errors to NaN
    return_cols = ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct']
    for col in return_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # Check expense ratio range
    invalid_expense = df[(df['expense_ratio_pct'] < 0.1) | (df['expense_ratio_pct'] > 2.5)]
    if not invalid_expense.empty:
        logging.warning(f"Found {len(invalid_expense)} funds with expense_ratio outside 0.1-2.5%. Clamping values.")
        df['expense_ratio_pct'] = df['expense_ratio_pct'].clip(lower=0.1, upper=2.5)
        
    out_path = PROCESSED_DIR / 'scheme_performance.csv'
    df.to_csv(out_path, index=False)
    logging.info(f"scheme_performance cleaned: {df.shape}")
    return df

def process_passthrough_files():
    """Copy other files to processed with minimal changes."""
    passthrough_files = [
        '01_fund_master.csv', '03_aum_by_fund_house.csv', '04_monthly_sip_inflows.csv',
        '05_category_inflows.csv', '06_industry_folio_count.csv', '09_portfolio_holdings.csv',
        '10_benchmark_indices.csv'
    ]
    dfs = {}
    for f in passthrough_files:
        path = RAW_DIR / f
        if path.exists():
            df = pd.read_csv(path)
            clean_name = f.split('_', 1)[1]
            out_path = PROCESSED_DIR / clean_name
            df.to_csv(out_path, index=False)
            dfs[clean_name.replace('.csv', '')] = df
            logging.info(f"Processed {f} -> {clean_name}")
    return dfs

def load_to_sqlite():
    engine = create_engine(f'sqlite:///{DB_PATH}')
    setup_db(engine)
    
    # Clean datasets
    nav_df = clean_nav_history()
    txn_df = clean_investor_transactions()
    perf_df = clean_scheme_performance()
    other_dfs = process_passthrough_files()
    
    # Generate dim_date
    if nav_df is not None:
        min_date = nav_df['date'].min()
        max_date = nav_df['date'].max()
        dim_date = generate_dim_date(min_date, max_date)
        dim_date.to_sql('dim_date', engine, if_exists='replace', index=False)
        logging.info(f"Loaded dim_date: {dim_date.shape}")
    
    # Load explicit tables
    if other_dfs.get('fund_master') is not None:
        other_dfs['fund_master'].to_sql('dim_fund', engine, if_exists='append', index=False)
        logging.info(f"Loaded dim_fund: {other_dfs['fund_master'].shape}")
        
    if nav_df is not None:
        nav_df[['amfi_code', 'date', 'nav']].to_sql('fact_nav', engine, if_exists='append', index=False)
        logging.info("Loaded fact_nav")
        
    if txn_df is not None:
        # Drop ID to let AUTOINCREMENT work, or pass it directly
        txn_df.to_sql('fact_transactions', engine, if_exists='append', index=False)
        logging.info("Loaded fact_transactions")
        
    if perf_df is not None:
        perf_cols = ['amfi_code', 'return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct', 'alpha', 'beta', 'sharpe_ratio', 'sortino_ratio', 'std_dev_ann_pct', 'max_drawdown_pct', 'aum_crore', 'expense_ratio_pct', 'morningstar_rating', 'risk_grade']
        perf_df[perf_cols].to_sql('fact_performance', engine, if_exists='append', index=False)
        logging.info("Loaded fact_performance")
        
    if other_dfs.get('aum_by_fund_house') is not None:
        other_dfs['aum_by_fund_house'].to_sql('fact_aum', engine, if_exists='append', index=False)
        logging.info("Loaded fact_aum")
        
    engine.dispose()

if __name__ == '__main__':
    load_to_sqlite()
