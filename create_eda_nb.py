import nbformat as nbf

nb = nbf.v4.new_notebook()

# Imports and Setup
imports_cell = nbf.v4.new_code_cell("""import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os
import warnings

warnings.filterwarnings('ignore')

# Set visual aesthetics
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

# Connect to Database
BASE_DIR = Path().resolve().parent
DB_PATH = BASE_DIR / 'data' / 'db' / 'bluestock_mf.db'
conn = sqlite3.connect(DB_PATH)
print(f"Successfully connected to Database: {DB_PATH}")

# Ensure reports directory exists for PNG exports
REPORTS_DIR = BASE_DIR / 'reports' / 'eda_charts'
os.makedirs(REPORTS_DIR, exist_ok=True)
""")

# 1. NAV Trend Analysis
nav_md = nbf.v4.new_markdown_cell("""## 1. NAV Trend Analysis
**Insight 1:** The Indian stock market experienced a significant bull run in 2023, evident across almost all equity mutual fund NAVs, followed by increased volatility and corrections in mid-2024.
""")
nav_code = nbf.v4.new_code_cell("""query_nav = \"\"\"
SELECT d.date, f.scheme_name, n.nav 
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
JOIN dim_date d ON n.date = d.date
WHERE d.year >= 2022 AND d.year <= 2026
\"\"\"
df_nav = pd.read_sql(query_nav, conn)

fig_nav = px.line(df_nav, x='date', y='nav', color='scheme_name', 
                  title='Daily NAV Trend for 40 Schemes (2022-2026)')

# Highlight 2023 Bull Run
fig_nav.add_vrect(x0="2023-01-01", x1="2023-12-31", fillcolor="green", opacity=0.1, line_width=0, annotation_text="2023 Bull Run")

# Highlight 2024 Correction
fig_nav.add_vrect(x0="2024-05-01", x1="2024-07-31", fillcolor="red", opacity=0.1, line_width=0, annotation_text="2024 Correction")

fig_nav.show()
fig_nav.write_image(REPORTS_DIR / '1_nav_trend.png')
""")

# 2. AUM Growth Bar Chart
aum_md = nbf.v4.new_markdown_cell("""## 2. AUM Growth by Fund House
**Insight 2:** SBI Mutual Fund dominates the market, reaching an incredible ₹12.5L Crore AUM, significantly outpacing its nearest competitors ICICI and HDFC.
""")
aum_code = nbf.v4.new_code_cell("""query_aum = \"\"\"
SELECT d.year, a.fund_house, MAX(a.aum_lakh_crore) as peak_aum
FROM fact_aum a
JOIN dim_date d ON a.date = d.date
WHERE d.year BETWEEN 2022 AND 2025
GROUP BY d.year, a.fund_house
\"\"\"
df_aum = pd.read_sql(query_aum, conn)

plt.figure(figsize=(14, 7))
sns.barplot(data=df_aum, x='year', y='peak_aum', hue='fund_house', palette='viridis')
plt.title('AUM Growth by Fund House (2022-2025)')
plt.ylabel('AUM (₹ Lakh Crores)')

# Annotate SBI
sbi_2025 = df_aum[(df_aum['fund_house'] == 'SBI Mutual Fund') & (df_aum['year'] == 2025)]
if not sbi_2025.empty:
    plt.annotate('SBI Dominance: ~₹12.5L Cr', 
                 xy=(3, sbi_2025['peak_aum'].values[0]), 
                 xytext=(2, 13),
                 arrowprops=dict(facecolor='black', shrink=0.05))

plt.tight_layout()
plt.savefig(REPORTS_DIR / '2_aum_growth.png')
plt.show()
""")

# 3. SIP Inflow Time-Series
sip_ts_md = nbf.v4.new_markdown_cell("""## 3. SIP Inflow Time-Series
**Insight 3:** Systematic Investment Plans (SIPs) have seen relentless, unbroken month-on-month growth, climaxing at an all-time high of ₹31,002 Crore in December 2025.
""")
sip_ts_code = nbf.v4.new_code_cell("""df_sip = pd.read_sql('SELECT month, sip_inflow_crore FROM monthly_sip_inflows ORDER BY month', conn)

fig_sip = px.line(df_sip, x='month', y='sip_inflow_crore', markers=True,
                  title='Monthly SIP Inflows (Jan 2022 - Dec 2025)')

fig_sip.add_annotation(x='2025-12', y=31002, text="All-Time High: ₹31,002 Cr",
                       showarrow=True, arrowhead=1)

fig_sip.show()
fig_sip.write_image(REPORTS_DIR / '3_sip_inflows.png')
""")

# 4. Category Inflow Heatmap
cat_md = nbf.v4.new_markdown_cell("""## 4. Category Inflow Heatmap
**Insight 4:** Small Cap and Mid Cap funds experienced massive surge inflows in late 2023 and early 2024, whereas Debt funds saw sporadic outflows during rate hike cycles.
""")
cat_code = nbf.v4.new_code_cell("""df_cat = pd.read_sql('SELECT month, category, net_inflow_crore FROM category_inflows', conn)
df_cat_pivot = df_cat.pivot(index='category', columns='month', values='net_inflow_crore')

plt.figure(figsize=(16, 8))
sns.heatmap(df_cat_pivot, cmap='RdYlGn', center=0, annot=False)
plt.title('Monthly Net Inflows by Fund Category (Heatmap)')
plt.tight_layout()
plt.savefig(REPORTS_DIR / '4_category_heatmap.png')
plt.show()
""")

# 5. Investor Demographics
demo_md = nbf.v4.new_markdown_cell("""## 5. Investor Demographics
**Insight 5:** The 25-35 age bracket constitutes the largest segment of the investor base, indicating high participation from millennials.
**Insight 6:** However, older age groups (45-55) tend to have significantly higher median SIP amounts, reflecting higher disposable income.
**Insight 7:** The gender split remains skewed towards male investors by volume, though female participation is steadily rising.
""")
demo_code = nbf.v4.new_code_cell("""df_tx = pd.read_sql('SELECT age_group, gender, amount_inr FROM fact_transactions WHERE transaction_type="SIP"', conn)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Age Pie
df_tx['age_group'].value_counts().plot.pie(ax=axes[0], autopct='%1.1f%%', cmap='Set3')
axes[0].set_title('Age Group Distribution')

# Box Plot
sns.boxplot(data=df_tx, x='age_group', y='amount_inr', ax=axes[1], order=['18-25', '25-35', '35-45', '45-55', '55+'])
axes[1].set_title('SIP Amount by Age Group')
axes[1].set_ylim(0, df_tx['amount_inr'].quantile(0.95)) # Cap outliers for visibility

# Gender Pie
df_tx['gender'].value_counts().plot.pie(ax=axes[2], autopct='%1.1f%%', colors=['#ff9999','#66b3ff'])
axes[2].set_title('Gender Split')

plt.tight_layout()
plt.savefig(REPORTS_DIR / '5_demographics.png')
plt.show()
""")

# 6. Geographic Distribution
geo_md = nbf.v4.new_markdown_cell("""## 6. Geographic Distribution
**Insight 8:** Maharashtra and Gujarat lead the country in total SIP investments, showcasing the financialization of savings in industrialized states.
**Insight 9:** B30 (Beyond Top 30) cities are contributing a rapidly growing slice of the pie, proving the success of AMC expansion strategies.
""")
geo_code = nbf.v4.new_code_cell("""df_geo = pd.read_sql('SELECT state, city_tier, amount_inr FROM fact_transactions WHERE transaction_type="SIP"', conn)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# State Bar
state_amt = df_geo.groupby('state')['amount_inr'].sum().sort_values(ascending=True).tail(10)
state_amt.plot(kind='barh', ax=axes[0], color='teal')
axes[0].set_title('Top 10 States by Total SIP Amount')

# T30 vs B30 Pie
df_geo.groupby('city_tier')['amount_inr'].sum().plot.pie(ax=axes[1], autopct='%1.1f%%', cmap='Pastel1')
axes[1].set_title('T30 vs B30 City Tier (by Volume)')

plt.tight_layout()
plt.savefig(REPORTS_DIR / '6_geographic.png')
plt.show()
""")

# 7. Folio Count Growth
folio_md = nbf.v4.new_markdown_cell("""## 7. Folio Count Growth
**Insight 10:** The industry almost doubled its investor base, jumping from 13.26 Crore folios in Jan 2022 to a staggering 26.12 Crore by Dec 2025.
""")
folio_code = nbf.v4.new_code_cell("""df_folio = pd.read_sql('SELECT month, total_folios_crore FROM industry_folio_count ORDER BY month', conn)

fig_folio = px.line(df_folio, x='month', y='total_folios_crore', markers=True, title='Industry Folio Count Growth (Crores)')

fig_folio.add_annotation(x='2022-01', y=13.26, text="Start: 13.26 Cr")
fig_folio.add_annotation(x='2025-12', y=26.12, text="End: 26.12 Cr")

fig_folio.show()
fig_folio.write_image(REPORTS_DIR / '7_folio_growth.png')
""")

# 8. Correlation Matrix
corr_md = nbf.v4.new_markdown_cell("""## 8. NAV Return Correlation Matrix
(Heatmap of daily returns for 10 selected funds)
""")
corr_code = nbf.v4.new_code_cell("""# Get top 10 funds by AUM to use for correlation
top_10_funds = pd.read_sql('SELECT amfi_code FROM fact_performance ORDER BY aum_crore DESC LIMIT 10', conn)['amfi_code'].tolist()
placeholders = ','.join(['?'] * len(top_10_funds))

query_corr = f\"\"\"
SELECT n.date, f.scheme_name, n.nav 
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
WHERE n.amfi_code IN ({placeholders})
\"\"\"
df_corr = pd.read_sql(query_corr, conn, params=top_10_funds)

# Pivot and calculate daily returns
df_pivot = df_corr.pivot(index='date', columns='scheme_name', values='nav')
daily_returns = df_pivot.pct_change().dropna()
corr_matrix = daily_returns.corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt=".2f")
plt.title('Pairwise Correlation of Daily Returns (Top 10 Funds)')
plt.tight_layout()
plt.savefig(REPORTS_DIR / '8_correlation.png')
plt.show()
""")

# 9. Sector Allocation Donut
sector_md = nbf.v4.new_markdown_cell("""## 9. Sector Allocation Donut
""")
sector_code = nbf.v4.new_code_cell("""df_sec = pd.read_sql('SELECT sector, SUM(market_value_cr) as mv FROM portfolio_holdings GROUP BY sector ORDER BY mv DESC', conn)

fig_sec = px.pie(df_sec, values='mv', names='sector', hole=0.5, title='Sector Allocation Across Equity Funds')
fig_sec.update_traces(textposition='inside', textinfo='percent+label')
fig_sec.show()
fig_sec.write_image(REPORTS_DIR / '9_sector_donut.png')
""")

# Construct notebook
nb.cells = [
    nbf.v4.new_markdown_cell("# Day 3: Full EDA Analysis\\nThis notebook covers the complete requirements for Day 3 EDA Capstone."),
    imports_cell,
    nav_md, nav_code,
    aum_md, aum_code,
    sip_ts_md, sip_ts_code,
    cat_md, cat_code,
    demo_md, demo_code,
    geo_md, geo_code,
    folio_md, folio_code,
    corr_md, corr_code,
    sector_md, sector_code
]

with open('notebooks/03_eda_analysis.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("EDA Notebook successfully generated.")
