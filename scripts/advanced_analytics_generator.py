import pandas as pd
import numpy as np
import nbformat as nbf
import matplotlib.pyplot as plt
import os
import warnings

warnings.filterwarnings('ignore')

data_dir = r"d:\python\bluestock_mf_capstone\data\processed"
output_dir = r"d:\python\bluestock_mf_capstone"

# 1. Load Data
print("Loading data...")
nav_history = pd.read_csv(os.path.join(data_dir, 'nav_history.csv'))
nav_history['date'] = pd.to_datetime(nav_history['date'])

fund_master = pd.read_csv(os.path.join(data_dir, 'fund_master.csv'))

transactions = pd.read_csv(os.path.join(data_dir, 'investor_transactions.csv'))
transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'])

holdings = pd.read_csv(os.path.join(data_dir, 'portfolio_holdings.csv'))

# Pivot NAV
nav_pivot = nav_history.pivot(index='date', columns='amfi_code', values='nav').sort_index()
returns = nav_pivot.pct_change()

# TASK 1: VaR and CVaR
print("Calculating VaR and CVaR...")
var_cvar_data = []
for col in returns.columns:
    ret = returns[col].dropna()
    if len(ret) > 0:
        var_95 = np.percentile(ret, 5)
        cvar_95 = ret[ret <= var_95].mean()
        var_cvar_data.append({'fund_id': col, 'VaR_95': var_95, 'CVaR_95': cvar_95})

var_cvar_df = pd.DataFrame(var_cvar_data)
var_cvar_df = var_cvar_df.merge(fund_master[['amfi_code', 'scheme_name']], left_on='fund_id', right_on='amfi_code')
var_cvar_df.rename(columns={'scheme_name': 'fund_name'}, inplace=True)
var_cvar_df = var_cvar_df[['fund_id', 'fund_name', 'VaR_95', 'CVaR_95']]
var_cvar_df.sort_values('VaR_95', ascending=True, inplace=True) # Most negative VaR first
var_cvar_df.to_csv(os.path.join(output_dir, 'var_cvar_report.csv'), index=False)

# TASK 2: Rolling 90-Day Sharpe
print("Calculating Rolling Sharpe...")
rolling_mean = returns.rolling(90).mean()
rolling_std = returns.rolling(90).std()
rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(252)

# Overall Sharpe for recommender
ann_ret = returns.mean() * 252
ann_vol = returns.std() * np.sqrt(252)
overall_sharpe = ann_ret / ann_vol
overall_sharpe_df = overall_sharpe.reset_index()
overall_sharpe_df.columns = ['amfi_code', 'Sharpe_Ratio']
overall_sharpe_df = overall_sharpe_df.merge(fund_master[['amfi_code', 'scheme_name', 'risk_category']], on='amfi_code')

# Pick 5 key funds (e.g. top 5 by overall sharpe among those with enough data)
top_5_amfi = overall_sharpe.dropna().sort_values(ascending=False).head(5).index
plt.figure(figsize=(12, 6))
for amfi in top_5_amfi:
    fname = fund_master[fund_master['amfi_code'] == amfi]['scheme_name'].iloc[0]
    plt.plot(rolling_sharpe.index, rolling_sharpe[amfi], label=fname)

plt.title('Rolling 90-Day Sharpe Ratio for Top 5 Funds')
plt.xlabel('Date')
plt.ylabel('Rolling Sharpe Ratio')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'rolling_sharpe_chart.png'), dpi=300)

# TASK 3: Investor Cohort Analysis
print("Calculating Cohort Analysis...")
cohorts = transactions.groupby('investor_id')['transaction_date'].min().dt.year.reset_index()
cohorts.columns = ['investor_id', 'cohort_year']
trans_cohort = transactions.merge(cohorts, on='investor_id')

cohort_stats = []
for year, group in trans_cohort.groupby('cohort_year'):
    investor_count = group['investor_id'].nunique()
    avg_sip = group[group['transaction_type'] == 'SIP']['amount_inr'].mean()
    total_invested = group['amount_inr'].sum()
    avg_invest_per_inv = total_invested / investor_count
    top_fund_id = group.groupby('amfi_code')['amount_inr'].sum().idxmax()
    top_fund = fund_master[fund_master['amfi_code'] == top_fund_id]['scheme_name'].iloc[0]
    
    cohort_stats.append({
        'cohort_year': year,
        'investor_count': investor_count,
        'avg_sip_amount': avg_sip,
        'total_invested': total_invested,
        'avg_investment_per_investor': avg_invest_per_inv,
        'top_fund': top_fund
    })
cohort_df = pd.DataFrame(cohort_stats)
print(cohort_df)

# TASK 4: SIP Continuity Analysis
print("Calculating SIP Continuity...")
sip_tx = transactions[transactions['transaction_type'] == 'SIP'].copy()
sip_counts = sip_tx.groupby('investor_id').size()
eligible_investors = sip_counts[sip_counts >= 6].index

sip_eligible = sip_tx[sip_tx['investor_id'].isin(eligible_investors)].sort_values(['investor_id', 'transaction_date'])
sip_eligible['prev_date'] = sip_eligible.groupby('investor_id')['transaction_date'].shift(1)
sip_eligible['gap_days'] = (sip_eligible['transaction_date'] - sip_eligible['prev_date']).dt.days

sip_gaps = sip_eligible.groupby('investor_id').agg(
    sip_count=('transaction_date', 'count'),
    avg_gap_days=('gap_days', 'mean')
).reset_index()

sip_gaps['status'] = np.where(sip_gaps['avg_gap_days'] > 35, 'at-risk', 'healthy')

total_eligible = len(sip_gaps)
healthy_count = len(sip_gaps[sip_gaps['status'] == 'healthy'])
at_risk_count = len(sip_gaps[sip_gaps['status'] == 'at-risk'])
continuity_rate = (healthy_count / total_eligible) * 100 if total_eligible > 0 else 0

print(f"Total Eligible: {total_eligible}, Healthy: {healthy_count}, At-Risk: {at_risk_count}, Continuity Rate: {continuity_rate:.2f}%")

# TASK 6: Sector Concentration (HHI)
print("Calculating HHI...")
equity_funds = fund_master[fund_master['category'] == 'Equity']['amfi_code'].unique()
holdings_eq = holdings[holdings['amfi_code'].isin(equity_funds)].copy()

hhi_data = []
for amfi, group in holdings_eq.groupby('amfi_code'):
    # Sum weights per sector in case there are multiple stocks in same sector
    sector_weights = group.groupby('sector')['weight_pct'].sum() / 100
    hhi = (sector_weights ** 2).sum()
    fname = fund_master[fund_master['amfi_code'] == amfi]['scheme_name'].iloc[0]
    hhi_data.append({'fund_name': fname, 'HHI': hhi})

hhi_df = pd.DataFrame(hhi_data).sort_values('HHI', ascending=False)
top_5_conc = hhi_df.head(5)
top_5_div = hhi_df.tail(5)

# Save recommender data
overall_sharpe_df.to_csv(os.path.join(output_dir, 'recommender_data.csv'), index=False)

print("Analytics generator completed successfully.")
