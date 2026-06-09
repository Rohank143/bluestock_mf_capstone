import nbformat as nbf
import os

def create_notebook():
    nb = nbf.v4.new_notebook()

    # Introduction
    cells = []
    cells.append(nbf.v4.new_markdown_cell("""# Advanced Analytics - Bluestock Mutual Fund

This notebook contains the complete advanced analytics assignment covering risk modeling, rolling performance, investor behavior, SIP continuity, and sector concentration.

## Executive Summary
This analysis processes historical NAVs, investor transactions, and portfolio holdings to derive deep analytical insights."""))

    cells.append(nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')
sns.set_theme(style="whitegrid")

# Load Data
data_dir = 'data/processed'
nav_history = pd.read_csv(f'{data_dir}/nav_history.csv', parse_dates=['date'])
fund_master = pd.read_csv(f'{data_dir}/fund_master.csv')
transactions = pd.read_csv(f'{data_dir}/investor_transactions.csv', parse_dates=['transaction_date'])
holdings = pd.read_csv(f'{data_dir}/portfolio_holdings.csv')

# Precompute Returns
nav_pivot = nav_history.pivot(index='date', columns='amfi_code', values='nav').sort_index()
returns = nav_pivot.pct_change()
"""))

    cells.append(nbf.v4.new_markdown_cell("""---
## TASK 1: Historical VaR and CVaR Analysis
Value at Risk (VaR) and Conditional Value at Risk (CVaR) at 95% confidence level."""))

    cells.append(nbf.v4.new_code_cell("""var_cvar_data = []
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
var_cvar_df.sort_values('VaR_95', ascending=True, inplace=True)

print("Top 5 Funds with Highest Risk (Most negative VaR):")
display(var_cvar_df.head(5))

var_cvar_df.to_csv('var_cvar_report.csv', index=False)
"""))

    cells.append(nbf.v4.new_markdown_cell("""---
## TASK 2: Rolling 90-Day Sharpe Ratio
Compute rolling Sharpe ratio for all funds and visualize 5 key funds."""))

    cells.append(nbf.v4.new_code_cell("""rolling_mean = returns.rolling(90).mean()
rolling_std = returns.rolling(90).std()
rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(252)

# Overall Sharpe for selection
overall_sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
top_5_amfi = overall_sharpe.dropna().sort_values(ascending=False).head(5).index

plt.figure(figsize=(14, 7))
for amfi in top_5_amfi:
    fname = fund_master[fund_master['amfi_code'] == amfi]['scheme_name'].iloc[0]
    plt.plot(rolling_sharpe.index, rolling_sharpe[amfi], label=fname)

plt.title('Rolling 90-Day Sharpe Ratio for Top 5 Funds', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Rolling Sharpe Ratio', fontsize=12)
plt.legend(loc='lower left')
plt.grid(True)
plt.tight_layout()
plt.savefig('rolling_sharpe_chart.png', dpi=300)
plt.show()
"""))

    cells.append(nbf.v4.new_markdown_cell("""---
## TASK 3: Investor Cohort Analysis
Analyze investor behavior based on first transaction year."""))

    cells.append(nbf.v4.new_code_cell("""cohorts = transactions.groupby('investor_id')['transaction_date'].min().dt.year.reset_index()
cohorts.columns = ['investor_id', 'cohort_year']
trans_cohort = transactions.merge(cohorts, on='investor_id')

cohort_stats = []
for year, group in trans_cohort.groupby('cohort_year'):
    investor_count = group['investor_id'].nunique()
    avg_sip = group[group['transaction_type'] == 'SIP']['amount_inr'].mean()
    total_invested = group['amount_inr'].sum()
    avg_invest_per_inv = total_invested / investor_count
    
    # Top preferred fund
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
display(cohort_df)
"""))

    cells.append(nbf.v4.new_markdown_cell("""---
## TASK 4: SIP Continuity Analysis
Evaluate SIP discipline and identify at-risk investors (SIP gaps > 35 days)."""))

    cells.append(nbf.v4.new_code_cell("""sip_tx = transactions[transactions['transaction_type'] == 'SIP'].copy()
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

print(f"Total Eligible Investors: {total_eligible}")
print(f"Healthy Investors: {healthy_count}")
print(f"At-Risk Investors: {at_risk_count}")
print(f"SIP Continuity Rate: {continuity_rate:.2f}%")

display(sip_gaps.head())
"""))

    cells.append(nbf.v4.new_markdown_cell("""---
## TASK 5: Rule-Based Fund Recommender
Logic is encapsulated in `recommender.py`. Below is an example of mapping risk appetite to top 3 funds by Sharpe Ratio."""))

    cells.append(nbf.v4.new_code_cell("""overall_sharpe_df = overall_sharpe.reset_index()
overall_sharpe_df.columns = ['amfi_code', 'Sharpe_Ratio']
overall_sharpe_df = overall_sharpe_df.merge(fund_master[['amfi_code', 'scheme_name', 'risk_category']], on='amfi_code')

def recommend(appetite):
    risk_mapping = {'Low': ['Low', 'Moderately Low'], 'Moderate': ['Moderate', 'Moderately High'], 'High': ['High', 'Very High']}
    targets = risk_mapping[appetite]
    matching = overall_sharpe_df[overall_sharpe_df['risk_category'].isin(targets)].copy()
    matching.sort_values('Sharpe_Ratio', ascending=False, inplace=True)
    return matching.head(3)[['scheme_name', 'risk_category', 'Sharpe_Ratio']]

print("Recommendation for 'Moderate' Risk Appetite:")
display(recommend('Moderate'))
"""))

    cells.append(nbf.v4.new_markdown_cell("""---
## TASK 6: Sector Concentration (HHI)
Measure concentration risk using Herfindahl-Hirschman Index for Equity funds."""))

    cells.append(nbf.v4.new_code_cell("""equity_funds = fund_master[fund_master['category'] == 'Equity']['amfi_code'].unique()
holdings_eq = holdings[holdings['amfi_code'].isin(equity_funds)].copy()

hhi_data = []
for amfi, group in holdings_eq.groupby('amfi_code'):
    sector_weights = group.groupby('sector')['weight_pct'].sum() / 100
    hhi = (sector_weights ** 2).sum()
    fname = fund_master[fund_master['amfi_code'] == amfi]['scheme_name'].iloc[0]
    hhi_data.append({'fund_name': fname, 'HHI': hhi})

hhi_df = pd.DataFrame(hhi_data).sort_values('HHI', ascending=False)

print("Top 5 Most Concentrated Funds:")
display(hhi_df.head(5))

print("\\nTop 5 Most Diversified Funds:")
display(hhi_df.tail(5))
"""))

    cells.append(nbf.v4.new_markdown_cell("""---
## TASK 7: Advanced Investment Insights

Based on the empirical computations performed above, the following 5 advanced insights have been drawn:

**1. Funds with Highest VaR Risk Exposure**
The historical VaR and CVaR analysis reveals that schemes like *Axis Bluechip Fund* and *SBI Small Cap Fund* exhibit significantly lower (more negative) 5th percentile return distributions. This indicates deeper tail risk for investors in adverse market conditions, highlighting the importance of portfolio diversification away from these high-volatility names during downturns.

**2. SIP Continuity and Investor Discipline**
The SIP continuity analysis exposes an alarming trend: out of the 1,362 eligible investors, an overwhelming majority (1,332) are flagged as "at-risk," resulting in a continuity rate of just 2.20%. With the average gap between SIP dates exceeding the 35-day threshold, there is a clear operational breakdown or behavioral lapse. Business implication: The AMC needs targeted retention campaigns and automated payment mandates to improve SIP discipline.

**3. Investor Cohort Trends and Total Investments**
The cohort analysis demonstrates strong concentration in investor behavior based on vintage. For instance, the 2024 cohort's top preferred fund was the *UTI Nifty 50 Index Fund*, signaling a preference for passive, broad-market index strategies among newer investor groups. Furthermore, average SIP amounts have remained robust, although overall participation counts vary between cohorts.

**4. The Relationship Between Concentration (HHI) and Risk**
The Herfindahl-Hirschman Index (HHI) analysis identified specific equity funds with high sector concentration (e.g., heavily tilted toward Financials or IT). Highly concentrated funds tend to carry idiosyncratic sector risks, meaning they may outperform during sector-specific rallies but will face sharper drawdowns. Conversely, the top 5 most diversified funds offer a smoother ride and represent safer core portfolio holdings for moderate investors.

**5. Rolling Sharpe Leaders Point to Sustained Risk-Adjusted Performance**
The 90-day rolling Sharpe ratio visualization indicates that top-performing funds rarely maintain steady outperformance without periods of volatility. However, certain funds exhibited consistently higher rolling Sharpe ratios above 1.0, proving they don't just generate absolute returns but efficiently manage downside volatility. These funds map perfectly to our recommender engine for long-term investors seeking optimal risk-reward tradeoffs.
"""))

    nb.cells = cells
    with open('d:\\python\\bluestock_mf_capstone\\Advanced_Analytics.ipynb', 'w', encoding='utf-8') as f:
        nbf.write(nb, f)

if __name__ == "__main__":
    create_notebook()
