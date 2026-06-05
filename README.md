# Bluestock Fintech — Mutual Fund Analytics Capstone

End-to-End Data Engineering, ETL Pipeline & Interactive Dashboard
**Duration:** 7 Working Days | ~50–55 Hours
**Data:** 40 schemes, 87K+ rows, 4.5 years of NAV history

---

## Project Structure

```
bluestock_mf_capstone/
├── data/
│   ├── raw/           ← Original CSVs + mfapi.in downloads
│   ├── processed/     ← Cleaned, merged datasets
│   └── db/            ← bluestock_mf.db (SQLite) — gitignored
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb
├── scripts/
│   ├── data_ingestion.py   ← Load + validate all 10 CSVs
│   ├── live_nav_fetch.py   ← Fetch live NAV from mfapi.in
│   ├── etl_pipeline.py     ← Master ETL (clean + load to DB)
│   ├── compute_metrics.py  ← Sharpe, Alpha, Beta, etc.
│   └── recommender.py      ← Fund recommendation by risk grade
├── sql/
│   ├── schema.sql          ← CREATE TABLE statements
│   └── queries.sql         ← 10 analytical SQL queries
├── dashboard/
│   └── bluestock_mf.pbix   ← Power BI dashboard
├── reports/
│   ├── Final_Report.pdf
│   └── Presentation.pptx
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Place datasets in `data/raw/`
Required files:
- `01_fund_master.csv`
- `02_nav_history.csv`
- `03_aum_by_fund_house.csv`
- `04_monthly_sip_inflows.csv`
- `05_category_inflows.csv`
- `06_industry_folio_count.csv`
- `07_scheme_performance.csv`
- `08_investor_transactions.csv`
- `09_portfolio_holdings.csv`
- `10_benchmark_indices.csv`

### 3. Run Day 1 scripts
```bash
python scripts/data_ingestion.py     # Load + validate all 10 CSVs
python scripts/live_nav_fetch.py     # Fetch live NAV from mfapi.in
```

### 4. Run full ETL pipeline (Day 2+)
```bash
python scripts/etl_pipeline.py
```

---

## Data Sources

| Source | URL | Data |
|--------|-----|------|
| AMFI India | amfiindia.com | NAV, AUM, SIP data |
| mfapi.in | api.mfapi.in/mf/{code} | Historical NAV (JSON) |
| NSE India | nseindia.com | Nifty 50, Nifty 100 index |
| BSE India | bseindia.com | BSE SmallCap index |

---

## Key Metrics Computed
- **CAGR** (1yr, 3yr, 5yr)
- **Sharpe Ratio** (Rf = 6.5%, annualised with √252)
- **Sortino Ratio** (downside deviation only)
- **Alpha & Beta** (OLS vs Nifty 100)
- **Max Drawdown**
- **VaR & CVaR** (95% confidence, historical method)
- **Fund Composite Scorecard** (weighted rank model)

---

## Dashboard Pages (Power BI)
1. **Industry Overview** — Total AUM, SIP inflows, folio count
2. **Fund Performance** — Risk-return scatter, NAV vs benchmark
3. **Investor Analytics** — Demographics, geography, SIP vs lumpsum
4. **SIP & Market Trends** — SIP inflow vs Nifty, category heatmap

---

## Notes
- `*.db` files are gitignored. To recreate the database: `python scripts/etl_pipeline.py`
- All NAV values are anchored to real AMFI values from mfapi.in
- Investor transaction data is synthetically generated with real geographic distributions
- This project is for **educational purposes only** and does not constitute financial advice
