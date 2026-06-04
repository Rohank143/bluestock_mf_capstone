-- 1. Top 5 funds by AUM
SELECT f.scheme_name, p.aum_crore 
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month for a specific fund (e.g. HDFC Top 100 - 125497)
SELECT d.year, d.month, AVG(n.nav) as avg_nav
FROM fact_nav n
JOIN dim_date d ON n.date = d.date
WHERE n.amfi_code = 125497
GROUP BY d.year, d.month
ORDER BY d.year DESC, d.month DESC
LIMIT 12;

-- 3. SIP YoY growth
WITH YearlySIP AS (
    SELECT d.year, SUM(t.amount_inr) as total_sip
    FROM fact_transactions t
    JOIN dim_date d ON t.transaction_date = d.date
    WHERE t.transaction_type = 'SIP'
    GROUP BY d.year
)
SELECT year, total_sip, 
       LAG(total_sip) OVER (ORDER BY year) as prev_year_sip,
       ROUND(((total_sip - LAG(total_sip) OVER (ORDER BY year)) / LAG(total_sip) OVER (ORDER BY year)) * 100, 2) as yoy_growth_pct
FROM YearlySIP;

-- 4. SIP Transactions count by State
SELECT state, COUNT(transaction_id) as total_sips, SUM(amount_inr) as total_sip_amount
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY state
ORDER BY total_sip_amount DESC;

-- 5. Funds with expense_ratio < 1% and 5yr return > 15%
SELECT f.scheme_name, f.expense_ratio_pct, p.return_5yr_pct
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
WHERE f.expense_ratio_pct < 1.0 AND p.return_5yr_pct > 15.0
ORDER BY p.return_5yr_pct DESC;

-- 6. Highest Sharpe Ratio per Category
SELECT f.category, f.scheme_name, MAX(p.sharpe_ratio) as max_sharpe
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
GROUP BY f.category;

-- 7. Total Lumpsum vs SIP Inflows (From Transactions)
SELECT transaction_type, SUM(amount_inr) as total_inflow
FROM fact_transactions
WHERE transaction_type IN ('SIP', 'LUMPSUM')
GROUP BY transaction_type;

-- 8. Monthly AUM Growth by Fund House
SELECT d.year, d.month, a.fund_house, SUM(a.aum_crore) as total_aum
FROM fact_aum a
JOIN dim_date d ON a.date = d.date
GROUP BY d.year, d.month, a.fund_house
ORDER BY d.year, d.month;

-- 9. Top 5 Best performing Equity funds (3Yr Return)
SELECT f.scheme_name, p.return_3yr_pct, p.alpha
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE f.category = 'Equity'
ORDER BY p.return_3yr_pct DESC
LIMIT 5;

-- 10. Distribution of KYC Status among investors
SELECT kyc_status, COUNT(DISTINCT investor_id) as total_investors
FROM fact_transactions
GROUP BY kyc_status;
