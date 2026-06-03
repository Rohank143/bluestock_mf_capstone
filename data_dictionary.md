# Data Dictionary - Bluestock Mutual Fund

## Dimension Tables

### `dim_fund`
Stores static information about mutual fund schemes.
- **amfi_code** (INTEGER, PK): Unique AMFI identifier for the scheme.
- **fund_house** (TEXT): Name of the AMC (e.g. SBI Mutual Fund).
- **scheme_name** (TEXT): Full name of the mutual fund scheme.
- **category** (TEXT): Broad asset class (Equity, Debt, Hybrid).
- **sub_category** (TEXT): Specific category (Large Cap, Mid Cap).
- **plan** (TEXT): Direct or Regular plan.
- **launch_date** (DATE): Inception date of the scheme.
- **benchmark** (TEXT): Benchmark index used for performance tracking.
- **expense_ratio_pct** (REAL): Annual expense ratio (clamped between 0.1% and 2.5%).
- **exit_load_pct** (REAL): Penalty for early redemption.
- **min_sip_amount** (INTEGER): Minimum required amount for SIP.
- **min_lumpsum_amount** (INTEGER): Minimum required amount for Lumpsum.
- **fund_manager** (TEXT): Name of the principal fund manager.
- **risk_category** (TEXT): Broad risk profile.
- **sebi_category_code** (TEXT): Regulatory category code.

### `dim_date`
Calendar dimension used for time-based filtering and grouping.
- **date** (DATE, PK): Full date in YYYY-MM-DD.
- **year** (INTEGER): Year.
- **month** (INTEGER): Month (1-12).
- **day** (INTEGER): Day of the month.
- **quarter** (INTEGER): Quarter (1-4).
- **day_of_week** (INTEGER): Day of week (0=Monday).
- **is_weekend** (BOOLEAN): True if Saturday or Sunday.

## Fact Tables

### `fact_nav`
Stores daily Net Asset Value for schemes. Forward-filled for weekends/holidays.
- **amfi_code** (INTEGER, FK): Reference to `dim_fund`.
- **date** (DATE, FK): Reference to `dim_date`.
- **nav** (REAL): Cleaned Net Asset Value (>0).

### `fact_transactions`
Records of individual investor investments and redemptions.
- **transaction_id** (INTEGER, PK): Auto-incremented ID.
- **investor_id** (TEXT): Unique investor identifier.
- **transaction_date** (DATE, FK): Date of transaction.
- **amfi_code** (INTEGER, FK): Reference to `dim_fund`.
- **transaction_type** (TEXT): Standardized to SIP, LUMPSUM, REDEMPTION, or OTHER.
- **amount_inr** (REAL): Transaction amount (Validated >0).
- **state/city/city_tier** (TEXT): Investor location details.
- **age_group/gender** (TEXT): Demographics.
- **payment_mode** (TEXT): UPI, Netbanking, etc.
- **kyc_status** (TEXT): Cleaned to UPPERCASE.

### `fact_performance`
Calculated performance metrics per fund.
- **amfi_code** (INTEGER, PK): Reference to `dim_fund`.
- **return_1yr_pct / 3yr / 5yr** (REAL): Annualized returns.
- **alpha / beta** (REAL): Risk-adjusted performance vs benchmark.
- **sharpe_ratio / sortino_ratio** (REAL): Return per unit of risk.
- **std_dev_ann_pct** (REAL): Volatility.
- **aum_crore** (REAL): Assets under management.
- **risk_grade** (TEXT): Categorical risk metric.

### `fact_aum`
Monthly aggregated AUM tracking per Fund House.
- **date** (DATE, FK): Reporting date.
- **fund_house** (TEXT): AMC Name.
- **aum_lakh_crore** (REAL): AUM in Lakh Crores.
- **aum_crore** (REAL): AUM converted to Crores.
- **num_schemes** (INTEGER): Active scheme count.

## Summary Statistics


