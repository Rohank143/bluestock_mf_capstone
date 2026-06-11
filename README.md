# Bluestock Mutual Fund Capstone Project

## Project Overview
This repository contains the full end-to-end data engineering and analytics capstone project for Bluestock Mutual Funds. The primary objective is to ingest, standardize, and analyze a fragmented dataset encompassing 40 schemes.

### Key Features
1. **Automated ETL Pipeline**: Extracts data from static CSV dumps and live NAV prices from the AMFI API, transforms them into a cleaned state, and loads them into a Star Schema SQLite data warehouse.
2. **Exploratory Data Analysis (EDA)**: Comprehensive jupyter notebooks revealing trends like the 2023 Bull Run, SIP inflow growth, and demographic investment behaviors.
3. **Advanced Performance Analytics**: Computes critical financial metrics including 1Y/3Y/5Y CAGR, Sharpe Ratio, Alpha, Beta, Tracking Error, and Maximum Drawdown.
4. **Fund Recommender**: A CLI rule-based recommendation engine matching investor risk profiles to the top performing funds.
5. **Reporting**: Includes a robust 15-20 page PDF report and a 12-slide Executive Presentation highlighting the insights and architectural design.

## Setup Instructions

### Prerequisites
- Python 3.9+
- Pip package manager

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/bluestock-mf-capstone.git
   cd bluestock-mf-capstone
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## How to Run the Pipeline
We have condensed the entire data processing, analysis, and report generation sequence into a single master script.

To run the full pipeline:
```bash
python run_pipeline.py
```
This will sequentially execute:
1. ETL & Data Cleaning
2. Financial Analytics & Scoring
3. EDA Notebook Generation
4. PDF Report and Presentation Generation

## How to Open the Dashboard
The executive dashboard provides an interactive deep-dive into the fund performance.
1. Navigate to the `dashboard/` directory.
2. Open the `Bluestock_Dashboard.twbx` (Tableau) or `.pbix` (Power BI) file using the respective desktop application.
3. **Published Version**: The dashboard can also be viewed online at: 
   > [Published Dashboard Placeholder URL - User to update]

## Dataset Descriptions
The data is structured into raw, processed, and database layers:
- `dim_fund_master`: Reference dimensions for the 40 mutual fund schemes (Category, AMC, Expense Ratio).
- `dim_date`: Calendar dimension table.
- `fact_nav_history`: Daily Net Asset Value time-series data.
- `fact_aum`: Assets Under Management metrics.
- `fact_transactions`: Granular investor transactions (SIPs/Lumpsums).
- `portfolio_holdings`: Sector and asset allocation details.
- `monthly_sip_inflows`: Aggregate system-level inflows.
