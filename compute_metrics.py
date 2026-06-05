import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import nbformat as nbf
import os

# Set paths
DATA_DIR = 'data/processed'
NAV_PATH = os.path.join(DATA_DIR, 'nav_history.csv')
FUND_MASTER_PATH = os.path.join(DATA_DIR, 'fund_master.csv')
BENCHMARK_PATH = os.path.join(DATA_DIR, 'benchmark_indices.csv')
OUTPUT_SCORECARD = 'fund_scorecard.csv'
OUTPUT_ALPHA_BETA = 'alpha_beta.csv'
OUTPUT_CHART = 'benchmark_comparison_chart.png'
OUTPUT_NOTEBOOK = 'Performance_Analytics.ipynb'

# Notebook Generation Object
nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell("# Mutual Fund Performance Analytics"))
cells.append(nbf.v4.new_markdown_cell("## 1. Data Loading and Initial Preparation"))

cells.append(nbf.v4.new_code_cell("""\
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

nav_df = pd.read_csv('data/processed/nav_history.csv', parse_dates=['date'])
funds_df = pd.read_csv('data/processed/fund_master.csv')
benchmarks_df = pd.read_csv('data/processed/benchmark_indices.csv', parse_dates=['date'])

# Filter out empty amfi_codes if any
funds_df = funds_df.dropna(subset=['amfi_code'])
funds_df['amfi_code'] = funds_df['amfi_code'].astype(int)

# Pivot NAV data
nav_pivot = nav_df.pivot(index='date', columns='amfi_code', values='nav').sort_index()

# Forward fill missing values
nav_pivot = nav_pivot.fillna(method='ffill')
"""))

# Execute Data Loading locally
nav_df = pd.read_csv(NAV_PATH, parse_dates=['date'])
funds_df = pd.read_csv(FUND_MASTER_PATH)
funds_df = funds_df.dropna(subset=['amfi_code'])
funds_df['amfi_code'] = funds_df['amfi_code'].astype(int)
benchmarks_df = pd.read_csv(BENCHMARK_PATH, parse_dates=['date'])

nav_pivot = nav_df.pivot(index='date', columns='amfi_code', values='nav').sort_index()
nav_pivot = nav_pivot.ffill()

cells.append(nbf.v4.new_markdown_cell("## 2. Compute Daily Returns & Validate Distribution"))
cells.append(nbf.v4.new_code_cell("""\
# Compute daily returns: daily_return = nav_t / nav_t-1 - 1
daily_returns = nav_pivot.pct_change().dropna(how='all')

# Validate distribution looks reasonable for a sample fund
sample_fund = daily_returns.columns[0]
plt.figure(figsize=(10, 5))
sns.histplot(daily_returns[sample_fund].dropna(), bins=50, kde=True)
plt.title(f'Distribution of Daily Returns for Fund {sample_fund}')
plt.show()
"""))

# Execute Daily Returns locally
daily_returns = nav_pivot.pct_change().dropna(how='all')

cells.append(nbf.v4.new_markdown_cell("## 3. Compute CAGR for 1yr, 3yr, 5yr"))
cells.append(nbf.v4.new_code_cell("""\
def compute_cagr(nav_series, years):
    # Get closest trading day to 'years' ago
    end_date = nav_series.last_valid_index()
    if pd.isna(end_date):
        return np.nan
    start_date = end_date - pd.DateOffset(years=years)
    
    # Check if data exists for that start_date (approximate)
    available_data = nav_series.loc[start_date:end_date].dropna()
    if len(available_data) == 0:
        return np.nan
        
    start_nav = available_data.iloc[0]
    end_nav = available_data.iloc[-1]
    
    # Calculate actual fraction of years based on trading days available / 252 or absolute days
    actual_years = (available_data.index[-1] - available_data.index[0]).days / 365.25
    if actual_years < years * 0.9: # Need at least 90% of the duration
        return np.nan
        
    return (end_nav / start_nav) ** (1/actual_years) - 1

cagr_data = []
for col in nav_pivot.columns:
    cagr_1y = compute_cagr(nav_pivot[col], 1)
    cagr_3y = compute_cagr(nav_pivot[col], 3)
    cagr_5y = compute_cagr(nav_pivot[col], 5)
    cagr_data.append({'amfi_code': col, 'CAGR_1yr': cagr_1y, 'CAGR_3yr': cagr_3y, 'CAGR_5yr': cagr_5y})

cagr_df = pd.DataFrame(cagr_data)
"""))

# Execute CAGR locally
def compute_cagr(nav_series, years):
    end_date = nav_series.last_valid_index()
    if pd.isna(end_date):
        return np.nan
    start_date = end_date - pd.DateOffset(years=years)
    available_data = nav_series.loc[start_date:end_date].dropna()
    if len(available_data) == 0:
        return np.nan
    start_nav = available_data.iloc[0]
    end_nav = available_data.iloc[-1]
    actual_years = (available_data.index[-1] - available_data.index[0]).days / 365.25
    if actual_years < years * 0.9:
        return np.nan
    return (end_nav / start_nav) ** (1/actual_years) - 1

cagr_data = []
for col in nav_pivot.columns:
    cagr_1y = compute_cagr(nav_pivot[col], 1)
    cagr_3y = compute_cagr(nav_pivot[col], 3)
    cagr_5y = compute_cagr(nav_pivot[col], 5)
    cagr_data.append({'amfi_code': col, 'CAGR_1yr': cagr_1y, 'CAGR_3yr': cagr_3y, 'CAGR_5yr': cagr_5y})

cagr_df = pd.DataFrame(cagr_data)

cells.append(nbf.v4.new_markdown_cell("## 4. Sharpe Ratio & Sortino Ratio"))
cells.append(nbf.v4.new_code_cell("""\
Rf = 0.065 # 6.5% RBI repo rate proxy
daily_Rf = Rf / 252

ratios_data = []
for col in daily_returns.columns:
    ret = daily_returns[col].dropna()
    if len(ret) < 252:
        ratios_data.append({'amfi_code': col, 'Sharpe': np.nan, 'Sortino': np.nan})
        continue
        
    ann_ret = ret.mean() * 252
    ann_vol = ret.std() * np.sqrt(252)
    sharpe = (ann_ret - Rf) / ann_vol if ann_vol > 0 else np.nan
    
    # Sortino: downside deviation
    negative_rets = ret[ret < 0]
    downside_vol = negative_rets.std() * np.sqrt(252)
    sortino = (ann_ret - Rf) / downside_vol if downside_vol > 0 else np.nan
    
    ratios_data.append({'amfi_code': col, 'Sharpe': sharpe, 'Sortino': sortino})

ratios_df = pd.DataFrame(ratios_data)
"""))

# Execute Ratios locally
Rf = 0.065
ratios_data = []
for col in daily_returns.columns:
    ret = daily_returns[col].dropna()
    if len(ret) < 252:
        ratios_data.append({'amfi_code': col, 'Sharpe': np.nan, 'Sortino': np.nan})
        continue
    ann_ret = ret.mean() * 252
    ann_vol = ret.std() * np.sqrt(252)
    sharpe = (ann_ret - Rf) / ann_vol if ann_vol > 0 else np.nan
    negative_rets = ret[ret < 0]
    downside_vol = negative_rets.std() * np.sqrt(252)
    sortino = (ann_ret - Rf) / downside_vol if downside_vol > 0 else np.nan
    ratios_data.append({'amfi_code': col, 'Sharpe': sharpe, 'Sortino': sortino})

ratios_df = pd.DataFrame(ratios_data)

cells.append(nbf.v4.new_markdown_cell("## 5. Alpha, Beta, and Maximum Drawdown"))
cells.append(nbf.v4.new_code_cell("""\
# Prepare Nifty 100 for Alpha/Beta calculation
# Assume NIFTY 100 is available in benchmarks_df. If not, fallback to NIFTY50.
benchmark_name = 'NIFTY 100' if 'NIFTY 100' in benchmarks_df['index_name'].unique() else 'NIFTY50'
nifty_bench = benchmarks_df[benchmarks_df['index_name'] == benchmark_name].set_index('date')['close_value']
nifty_returns = nifty_bench.pct_change().dropna()

alpha_beta_dd_data = []

for col in nav_pivot.columns:
    # Max Drawdown
    nav_series = nav_pivot[col].dropna()
    running_max = nav_series.cummax()
    drawdown = (nav_series / running_max) - 1
    max_dd = drawdown.min()
    
    # Worst DD date range (rough approximation: min DD point)
    worst_dd_date = drawdown.idxmin()
    
    # Alpha & Beta
    ret = daily_returns[col].dropna()
    # Align dates
    aligned = pd.concat([ret, nifty_returns], axis=1).dropna()
    if len(aligned) > 100:
        fund_r = aligned.iloc[:, 0]
        bench_r = aligned.iloc[:, 1]
        slope, intercept, r_value, p_value, std_err = stats.linregress(bench_r, fund_r)
        beta = slope
        alpha = intercept * 252
    else:
        beta = np.nan
        alpha = np.nan
        
    alpha_beta_dd_data.append({
        'amfi_code': col, 
        'Alpha': alpha, 
        'Beta': beta, 
        'Max_Drawdown': max_dd,
        'Worst_DD_Date': worst_dd_date
    })

ab_dd_df = pd.DataFrame(alpha_beta_dd_data)
ab_dd_df.to_csv('alpha_beta.csv', index=False)
"""))

# Execute Alpha, Beta, Max Drawdown locally
benchmark_name = 'NIFTY 100' if 'NIFTY 100' in benchmarks_df['index_name'].unique() else 'NIFTY50'
nifty_bench = benchmarks_df[benchmarks_df['index_name'] == benchmark_name].set_index('date')['close_value']
nifty_returns = nifty_bench.pct_change().dropna()

alpha_beta_dd_data = []
for col in nav_pivot.columns:
    nav_series = nav_pivot[col].dropna()
    if len(nav_series) == 0:
        continue
    running_max = nav_series.cummax()
    drawdown = (nav_series / running_max) - 1
    max_dd = drawdown.min()
    worst_dd_date = drawdown.idxmin()
    
    ret = daily_returns[col].dropna()
    aligned = pd.concat([ret, nifty_returns], axis=1).dropna()
    if len(aligned) > 100:
        fund_r = aligned.iloc[:, 0]
        bench_r = aligned.iloc[:, 1]
        slope, intercept, r_value, p_value, std_err = stats.linregress(bench_r, fund_r)
        beta = slope
        alpha = intercept * 252
    else:
        beta = np.nan
        alpha = np.nan
        
    alpha_beta_dd_data.append({
        'amfi_code': col, 
        'Alpha': alpha, 
        'Beta': beta, 
        'Max_Drawdown': max_dd,
        'Worst_DD_Date': worst_dd_date
    })

ab_dd_df = pd.DataFrame(alpha_beta_dd_data)
ab_dd_df.to_csv(OUTPUT_ALPHA_BETA, index=False)

cells.append(nbf.v4.new_markdown_cell("## 6. Fund Scorecard (0–100)"))
cells.append(nbf.v4.new_code_cell("""\
# Combine all metrics
metrics_df = funds_df[['amfi_code', 'scheme_name', 'expense_ratio_pct']].merge(cagr_df, on='amfi_code', how='left')
metrics_df = metrics_df.merge(ratios_df, on='amfi_code', how='left')
metrics_df = metrics_df.merge(ab_dd_df, on='amfi_code', how='left')

# Rank metrics (1 is worst, N is best for positive metrics, inverse for expense/drawdown)
# Fillna with worst possible value for ranking to avoid bias
valid_funds = metrics_df.dropna(subset=['CAGR_3yr', 'Sharpe', 'Alpha', 'expense_ratio_pct', 'Max_Drawdown']).copy()

# Ranks (ascending=True means lowest value gets rank 1)
# 3yr return rank (higher is better) -> ascending=True makes lowest return rank 1
# Actually, rank(pct=True) gives percentile. We want rank from 1 to N
rank_3yr = valid_funds['CAGR_3yr'].rank()
rank_sharpe = valid_funds['Sharpe'].rank()
rank_alpha = valid_funds['Alpha'].rank()
# Inverse ranks: lower is better -> ascending=False makes lowest value get highest rank
rank_expense = valid_funds['expense_ratio_pct'].rank(ascending=False)
# Max DD is negative, closer to 0 is better. So higher value is better. 
# rank() default ascending=True makes more negative (worse DD) get lower rank. This is correct.
rank_dd = valid_funds['Max_Drawdown'].rank()

# Total number of valid funds
N = len(valid_funds)

# Normalize ranks to 0-100 scale: (rank - 1) / (N - 1) * 100
def norm_rank(series):
    if len(series) <= 1:
        return series
    return (series - 1) / (len(series) - 1) * 100

valid_funds['Score_3yr'] = norm_rank(rank_3yr) * 0.30
valid_funds['Score_Sharpe'] = norm_rank(rank_sharpe) * 0.25
valid_funds['Score_Alpha'] = norm_rank(rank_alpha) * 0.20
valid_funds['Score_Expense'] = norm_rank(rank_expense) * 0.15
valid_funds['Score_DD'] = norm_rank(rank_dd) * 0.10

valid_funds['Total_Score'] = (
    valid_funds['Score_3yr'] + 
    valid_funds['Score_Sharpe'] + 
    valid_funds['Score_Alpha'] + 
    valid_funds['Score_Expense'] + 
    valid_funds['Score_DD']
)

scorecard = valid_funds.sort_values(by='Total_Score', ascending=False)
scorecard.to_csv('fund_scorecard.csv', index=False)
"""))

# Execute Scorecard locally
metrics_df = funds_df[['amfi_code', 'scheme_name', 'expense_ratio_pct']].merge(cagr_df, on='amfi_code', how='left')
metrics_df = metrics_df.merge(ratios_df, on='amfi_code', how='left')
metrics_df = metrics_df.merge(ab_dd_df, on='amfi_code', how='left')

valid_funds = metrics_df.dropna(subset=['CAGR_3yr', 'Sharpe', 'Alpha', 'expense_ratio_pct', 'Max_Drawdown']).copy()
rank_3yr = valid_funds['CAGR_3yr'].rank()
rank_sharpe = valid_funds['Sharpe'].rank()
rank_alpha = valid_funds['Alpha'].rank()
rank_expense = valid_funds['expense_ratio_pct'].rank(ascending=False)
rank_dd = valid_funds['Max_Drawdown'].rank()

def norm_rank(series):
    if len(series) <= 1:
        return series
    return (series - 1) / (len(series) - 1) * 100

valid_funds['Score_3yr'] = norm_rank(rank_3yr) * 0.30
valid_funds['Score_Sharpe'] = norm_rank(rank_sharpe) * 0.25
valid_funds['Score_Alpha'] = norm_rank(rank_alpha) * 0.20
valid_funds['Score_Expense'] = norm_rank(rank_expense) * 0.15
valid_funds['Score_DD'] = norm_rank(rank_dd) * 0.10

valid_funds['Total_Score'] = (
    valid_funds['Score_3yr'] + 
    valid_funds['Score_Sharpe'] + 
    valid_funds['Score_Alpha'] + 
    valid_funds['Score_Expense'] + 
    valid_funds['Score_DD']
)

scorecard = valid_funds.sort_values(by='Total_Score', ascending=False)
scorecard.to_csv(OUTPUT_SCORECARD, index=False)


cells.append(nbf.v4.new_markdown_cell("## 7. Benchmark Comparison Chart & Tracking Error"))
cells.append(nbf.v4.new_code_cell("""\
# Top 5 funds
top_5_funds = scorecard.head(5)

# Benchmark comparison chart - plot top 5 funds vs Nifty 50 and Nifty 100 over 3 years
end_date = nav_pivot.index[-1]
start_date = end_date - pd.DateOffset(years=3)

# Filter benchmarks
nifty50 = benchmarks_df[benchmarks_df['index_name'] == 'NIFTY50'].set_index('date')['close_value'].loc[start_date:end_date]
# Not all benchmark datasets might have NIFTY 100, if missing fallback
has_nifty100 = 'NIFTY 100' in benchmarks_df['index_name'].unique()
if has_nifty100:
    nifty100 = benchmarks_df[benchmarks_df['index_name'] == 'NIFTY 100'].set_index('date')['close_value'].loc[start_date:end_date]

plt.figure(figsize=(14, 7))

# Normalize series to 100 at start date
if len(nifty50) > 0:
    plt.plot(nifty50 / nifty50.iloc[0] * 100, label='NIFTY 50', linewidth=2, color='black')
if has_nifty100 and len(nifty100) > 0:
    plt.plot(nifty100 / nifty100.iloc[0] * 100, label='NIFTY 100', linewidth=2, color='gray')

# Plot Top 5 funds
for idx, row in top_5_funds.iterrows():
    amfi = row['amfi_code']
    name = row['scheme_name']
    fund_nav = nav_pivot[amfi].loc[start_date:end_date].dropna()
    if len(fund_nav) > 0:
        plt.plot(fund_nav / fund_nav.iloc[0] * 100, label=name)
        
        # Tracking Error against Nifty 50
        fund_ret = daily_returns[amfi].loc[start_date:end_date].dropna()
        b_ret = nifty50.pct_change().dropna()
        aligned_te = pd.concat([fund_ret, b_ret], axis=1).dropna()
        if len(aligned_te) > 0:
            te = (aligned_te.iloc[:, 0] - aligned_te.iloc[:, 1]).std() * np.sqrt(252)
            print(f"Tracking Error for {name} vs NIFTY 50: {te:.4f}")

plt.title('Top 5 Funds vs Benchmarks (3 Years) - Rebased to 100')
plt.xlabel('Date')
plt.ylabel('Normalized NAV / Index Value')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('benchmark_comparison_chart.png')
plt.show()
"""))

# Execute Chart locally
top_5_funds = scorecard.head(5)
end_date = nav_pivot.index[-1]
start_date = end_date - pd.DateOffset(years=3)

nifty50 = benchmarks_df[benchmarks_df['index_name'] == 'NIFTY50'].set_index('date')['close_value'].loc[start_date:end_date]
has_nifty100 = 'NIFTY 100' in benchmarks_df['index_name'].unique()
if has_nifty100:
    nifty100 = benchmarks_df[benchmarks_df['index_name'] == 'NIFTY 100'].set_index('date')['close_value'].loc[start_date:end_date]

plt.figure(figsize=(14, 7))

if len(nifty50) > 0:
    plt.plot(nifty50 / nifty50.iloc[0] * 100, label='NIFTY 50', linewidth=2, color='black')
if has_nifty100 and len(nifty100) > 0:
    plt.plot(nifty100 / nifty100.iloc[0] * 100, label='NIFTY 100', linewidth=2, color='gray')

for idx, row in top_5_funds.iterrows():
    amfi = row['amfi_code']
    name = row['scheme_name']
    fund_nav = nav_pivot[amfi].loc[start_date:end_date].dropna()
    if len(fund_nav) > 0:
        plt.plot(fund_nav / fund_nav.iloc[0] * 100, label=name)
        
        fund_ret = daily_returns[amfi].loc[start_date:end_date].dropna()
        b_ret = nifty50.pct_change().dropna()
        aligned_te = pd.concat([fund_ret, b_ret], axis=1).dropna()
        if len(aligned_te) > 0:
            te = (aligned_te.iloc[:, 0] - aligned_te.iloc[:, 1]).std() * np.sqrt(252)

plt.title('Top 5 Funds vs Benchmarks (3 Years) - Rebased to 100')
plt.xlabel('Date')
plt.ylabel('Normalized NAV / Index Value')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_CHART)

# Write notebook
nb['cells'] = cells
with open(OUTPUT_NOTEBOOK, 'w') as f:
    nbf.write(nb, f)
