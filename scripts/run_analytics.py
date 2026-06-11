"""
Module: run_analytics.py
Description: Computes financial analytics and scores mutual funds, replacing prints with logging.
"""
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
warnings.filterwarnings('ignore')
sns.set_theme(style="whitegrid")

# Load data
nav_history = pd.read_csv('data/processed/nav_history.csv')
nav_history['date'] = pd.to_datetime(nav_history['date'])

benchmark = pd.read_csv('data/processed/benchmark_indices.csv')
benchmark['date'] = pd.to_datetime(benchmark['date'])

fund_master = pd.read_csv('data/processed/fund_master.csv')

# Pivot nav history for easier calculations
nav_pivot = nav_history.pivot(index='date', columns='amfi_code', values='nav')
nav_pivot.sort_index(inplace=True)

# Calculate daily returns
daily_returns = nav_pivot.pct_change().dropna(how='all')

# Flatten to plot distribution
all_returns = daily_returns.values.flatten()
all_returns = all_returns[~np.isnan(all_returns)]

mean_ret = np.mean(all_returns)
std_ret = np.std(all_returns)
skewness = stats.skew(all_returns)
kurtosis = stats.kurtosis(all_returns)
outliers = all_returns[(all_returns > mean_ret + 3 * std_ret) | (all_returns < mean_ret - 3 * std_ret)]

cagr_data = []
end_date = nav_pivot.index[-1]
start_1y = end_date - pd.DateOffset(years=1)
start_3y = end_date - pd.DateOffset(years=3)
start_5y = end_date - pd.DateOffset(years=5)

def calculate_cagr(start_val, end_val, years):
    """Calculate Compound Annual Growth Rate (CAGR)."""
    if start_val > 0 and years > 0:
        return (end_val / start_val) ** (1 / years) - 1
    return np.nan

for col in nav_pivot.columns:
    series = nav_pivot[col].dropna()
    if len(series) < 2:
        continue
        
    cagr_full = calculate_cagr(series.iloc[0], series.iloc[-1], (series.index[-1] - series.index[0]).days / 365.25)
    
    series_1y = series.loc[start_1y:]
    cagr_1y = calculate_cagr(series_1y.iloc[0], series_1y.iloc[-1], 1) if len(series_1y) > 0 else np.nan
        
    series_3y = series.loc[start_3y:]
    cagr_3y = calculate_cagr(series_3y.iloc[0], series_3y.iloc[-1], 3) if len(series_3y) > 0 else np.nan
        
    series_5y = series.loc[start_5y:]
    cagr_5y = calculate_cagr(series_5y.iloc[0], series_5y.iloc[-1], 5) if len(series_5y) > 0 else np.nan
        
    cagr_data.append({
        'amfi_code': col,
        'CAGR_Full': cagr_full,
        'CAGR_1Y': cagr_1y,
        'CAGR_3Y': cagr_3y,
        'CAGR_5Y': cagr_5y
    })

cagr_df = pd.DataFrame(cagr_data)

Rf = 0.065
TRADING_DAYS = 252

ratio_data = []
for col in daily_returns.columns:
    ret = daily_returns[col].dropna()
    if len(ret) < 2:
        continue
        
    ann_ret = ret.mean() * TRADING_DAYS
    ann_vol = ret.std() * np.sqrt(TRADING_DAYS)
    sharpe = (ann_ret - Rf) / ann_vol if ann_vol > 0 else np.nan
    
    neg_ret = ret[ret < 0]
    downside_vol = neg_ret.std() * np.sqrt(TRADING_DAYS) if len(neg_ret) > 1 else np.nan
    sortino = (ann_ret - Rf) / downside_vol if downside_vol and downside_vol > 0 else np.nan
    
    ratio_data.append({
        'amfi_code': col,
        'Ann_Return': ann_ret,
        'Ann_Volatility': ann_vol,
        'Sharpe': sharpe,
        'Sortino': sortino
    })

ratio_df = pd.DataFrame(ratio_data)

nifty100 = benchmark[benchmark['index_name'] == 'NIFTY 100'].copy()
if len(nifty100) == 0:
    nifty100 = benchmark[benchmark['index_name'] == 'NIFTY50'].copy()
nifty100.sort_values('date', inplace=True)
nifty100.set_index('date', inplace=True)
nifty100_ret = nifty100['close_value'].pct_change().dropna()

ab_dd_data = []
for col in nav_pivot.columns:
    series = nav_pivot[col].dropna()
    if len(series) < 2:
        continue
        
    running_max = series.cummax()
    drawdown = (series / running_max) - 1
    max_dd = drawdown.min()
    worst_dd_date = drawdown.idxmin()
    
    ret = daily_returns[col].dropna()
    aligned = pd.concat([ret, nifty100_ret], axis=1).dropna()
    
    if len(aligned) > 100:
        fund_r = aligned.iloc[:, 0]
        bench_r = aligned.iloc[:, 1]
        
        slope, intercept, _, _, _ = stats.linregress(bench_r, fund_r)
        beta = slope
        alpha = intercept * TRADING_DAYS
    else:
        beta = np.nan
        alpha = np.nan
        
    ab_dd_data.append({
        'amfi_code': col,
        'Alpha': alpha,
        'Beta': beta,
        'Max_Drawdown': max_dd,
        'Worst_DD_Date': worst_dd_date
    })

ab_dd_df = pd.DataFrame(ab_dd_data)
ab_dd_df.to_csv('alpha_beta.csv', index=False)

metrics_df = fund_master[['amfi_code', 'scheme_name', 'expense_ratio_pct']].merge(cagr_df, on='amfi_code', how='left')
metrics_df = metrics_df.merge(ratio_df, on='amfi_code', how='left')
metrics_df = metrics_df.merge(ab_dd_df, on='amfi_code', how='left')

valid_funds = metrics_df.dropna(subset=['CAGR_3Y', 'Sharpe', 'Alpha', 'expense_ratio_pct', 'Max_Drawdown']).copy()

rank_3yr = valid_funds['CAGR_3Y'].rank(ascending=True)
rank_sharpe = valid_funds['Sharpe'].rank(ascending=True)
rank_alpha = valid_funds['Alpha'].rank(ascending=True)
rank_expense = valid_funds['expense_ratio_pct'].rank(ascending=False)
rank_dd = valid_funds['Max_Drawdown'].rank(ascending=True)

def normalize_rank(series):
    """Normalize a series of ranks to a 0-100 scale."""
    return (series - 1) / (len(series) - 1) * 100

valid_funds['Score_3Y'] = normalize_rank(rank_3yr) * 0.30
valid_funds['Score_Sharpe'] = normalize_rank(rank_sharpe) * 0.25
valid_funds['Score_Alpha'] = normalize_rank(rank_alpha) * 0.20
valid_funds['Score_Expense'] = normalize_rank(rank_expense) * 0.15
valid_funds['Score_DD'] = normalize_rank(rank_dd) * 0.10

valid_funds['Composite_Score'] = (
    valid_funds['Score_3Y'] + 
    valid_funds['Score_Sharpe'] + 
    valid_funds['Score_Alpha'] + 
    valid_funds['Score_Expense'] + 
    valid_funds['Score_DD']
)

scorecard = valid_funds.sort_values('Composite_Score', ascending=False)
scorecard.to_csv('fund_scorecard.csv', index=False)

top_5 = scorecard.head(5)

nifty50 = benchmark[benchmark['index_name'] == 'NIFTY50'].set_index('date')['close_value']
nifty100 = benchmark[benchmark['index_name'] == 'NIFTY 100'].set_index('date')['close_value']

n50_3y = nifty50.loc[start_3y:end_date]
n100_3y = nifty100.loc[start_3y:end_date]

n50_ret = n50_3y.pct_change().dropna()
n100_ret = n100_3y.pct_change().dropna()

plt.figure(figsize=(14, 8))

if len(n50_3y) > 0:
    plt.plot(n50_3y / n50_3y.iloc[0] * 100, label='NIFTY 50', color='black', linewidth=2.5)
if len(n100_3y) > 0:
    plt.plot(n100_3y / n100_3y.iloc[0] * 100, label='NIFTY 100', color='gray', linewidth=2.5, linestyle='--')

for _, row in top_5.iterrows():
    amfi = row['amfi_code']
    name = row['scheme_name']
    
    f_nav = nav_pivot[amfi].loc[start_3y:end_date].dropna()
    if len(f_nav) > 0:
        plt.plot(f_nav / f_nav.iloc[0] * 100, label=name)
        
        f_ret = daily_returns[amfi].loc[start_3y:end_date].dropna()
        
        al_50 = pd.concat([f_ret, n50_ret], axis=1).dropna()
        if len(al_50) > 0:
            te_50 = (al_50.iloc[:, 0] - al_50.iloc[:, 1]).std() * np.sqrt(252)
            logging.info(f"Tracking Error ({name} vs NIFTY 50): {te_50:.4f}")
            
        al_100 = pd.concat([f_ret, n100_ret], axis=1).dropna()
        if len(al_100) > 0:
            te_100 = (al_100.iloc[:, 0] - al_100.iloc[:, 1]).std() * np.sqrt(252)
            logging.info(f"Tracking Error ({name} vs NIFTY 100): {te_100:.4f}")

plt.title('Top 5 Funds vs Benchmarks (3 Years)', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Rebased Value (100 at Start)', fontsize=12)
plt.legend(loc='upper left')
plt.tight_layout()
plt.savefig('benchmark_comparison_chart.png', dpi=300)
