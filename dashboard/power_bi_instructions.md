# Power BI Dashboard Development Guide

This guide provides the necessary data mapping and DAX formulas to build the `bluestock_mf_dashboard.pbix` exactly as requested. Since the AI cannot generate the binary proprietary `.pbix` file containing layouts directly, use this guide alongside the visual mockups provided (`Dashboard.pdf`) to quickly construct the dashboard.

## 1. Data Connection
1. Open Power BI Desktop.
2. Click **Get Data** -> **ODBC** (if using SQLite ODBC Driver) or select **Blank Query** and use an R/Python script to connect to `data/db/bluestock_mf.db`. Alternatively, load the CSVs from `data/processed/`.
3. Load the following tables:
   - `fact_transactions`
   - `fact_performance`
   - `fact_aum`
   - `fact_nav`
   - `dim_fund`
   - `dim_date`
   - `monthly_sip_inflows`
   - `category_inflows`

## 2. Data Modeling
In the Model view, establish the following relationships:
- `fact_transactions[amfi_code]` <-> `dim_fund[amfi_code]` (Many to One)
- `fact_transactions[transaction_date]` <-> `dim_date[date]` (Many to One)
- `fact_performance[amfi_code]` <-> `dim_fund[amfi_code]` (One to One)
- `fact_nav[amfi_code]` <-> `dim_fund[amfi_code]` (Many to One)

## 3. DAX Formulas (KPIs)

Create the following explicit measures for the KPI cards:

```dax
// Total AUM (Page 1)
Total_AUM_Lakh_Cr = SUM(fact_aum[aum_lakh_crore])
// Format this as Rs. 81L Cr

// SIP Inflows (Page 1 & 4)
Total_SIP_Inflow_Cr = SUM(monthly_sip_inflows[sip_inflow_crore])

// Total Folios (Page 1)
Total_Folios_Cr = MAX(industry_folio_count[total_folios_crore]) // Assuming max date

// Total Schemes (Page 1)
Total_Schemes = DISTINCTCOUNT(dim_fund[amfi_code])

// SIP Account Growth YoY (Page 4)
SIP_YoY_Growth = AVERAGE(monthly_sip_inflows[yoy_growth_pct])
```

## 4. Page by Page Setup

### PAGE 1 — Industry Overview
- **Visuals**:
  - 4 x Card visuals using the KPIs above.
  - **Line Chart**: Axis = `date`, Values = `Total AUM`.
  - **Bar Chart**: Y-Axis = `fund_house`, X-Axis = `Total AUM`, Top N filter applied to Fund House (Top 10).

### PAGE 2 — Fund Performance
- **Scatter Plot**: X-Axis = `return_3yr_pct`, Y-Axis = `std_dev_ann_pct`, Size = `aum_crore`, Legend = `category`.
- **Table**: Select fields from `dim_fund` and `fact_performance` (Return, Risk, Alpha, Beta).
- **Line Chart (Drill-through)**: Axis = `date`, Values = `nav` (from `fact_nav`). Set up a drill-through filter from the Fund table to this chart.
- **Slicers**: `fund_house`, `category`, `plan`.

### PAGE 3 — Investor Analytics
- **Map / Bar Chart**: Location = `state`, Values = Sum of `amount_inr` from `fact_transactions`.
- **Donut Chart**: Legend = `transaction_type`, Values = Sum of `amount_inr`.
- **Clustered Bar Chart**: X-Axis = `age_group`, Values = Average of `amount_inr` (Filter visual to Transaction Type = "SIP").
- **Line Chart**: Axis = `transaction_date` (Month/Year), Values = Sum of `amount_inr` (Count of Volume).
- **Slicers**: `state`, `age_group`, `city_tier`.

### PAGE 4 — SIP & Market Trends
- **Dual-axis Line & Clustered Column Chart**: Column = `sip_inflow_crore` (from `monthly_sip_inflows`), Line = NIFTY 50 Close value.
- **Matrix (Heat Map)**: Rows = `category`, Columns = `month`, Values = `net_inflow_crore`. Apply Conditional Formatting (Background color scale) to the Values.
- **Bar Chart**: Y-Axis = `category`, X-Axis = `net_inflow_crore`. Apply Top 5 filter on Category.
- **KPI Card**: SIP Accounts growth YoY.

## 5. Formatting & Polish
1. **Theme**: Apply a Custom Theme to match the Bluestock colors (Blues, Greens, and White backgrounds).
2. **Tooltips**: Create a custom tooltip page and assign it to the Scatter Plot and Matrix to show additional fund details.
3. **Logo**: Insert -> Image -> (Bluestock Logo).
4. **Publish**: Save as `.pbix` and Export to PDF (`File -> Export -> Export to PDF`).
