import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import os

DB_PATH = 'data/db/bluestock_mf.db'
OUT_DIR = 'dashboard'

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.figsize'] = (14, 8)

conn = sqlite3.connect(DB_PATH)

def add_bluestock_branding(fig, title):
    fig.suptitle(title, fontsize=20, fontweight='bold', color='#1f77b4', ha='left', x=0.05, y=0.96)
    fig.text(0.95, 0.95, "Bluestock MF Capstone", fontsize=12, color='gray', ha='right', fontweight='bold')
    plt.subplots_adjust(top=0.88, hspace=0.4, wspace=0.3)

# ----------------- PAGE 1: Industry Overview -----------------
def generate_page_1():
    fig = plt.figure(figsize=(16, 9))
    add_bluestock_branding(fig, "PAGE 1: Industry Overview")
    
    # KPIs Layout
    kpi_ax = plt.subplot2grid((3, 2), (0, 0), colspan=2)
    kpi_ax.axis('off')
    kpis = [
        ("Total AUM", "₹81L Cr"),
        ("SIP Inflows", "₹31K Cr"),
        ("Total Folios", "26.12 Cr"),
        ("Total Schemes", "1908")
    ]
    for i, (label, val) in enumerate(kpis):
        kpi_ax.text(0.12 + i*0.25, 0.5, val, fontsize=24, fontweight='bold', ha='center', color='#2ca02c')
        kpi_ax.text(0.12 + i*0.25, 0.2, label, fontsize=14, ha='center', color='#555')
        
    # Line chart: Industry AUM
    try:
        aum_df = pd.read_sql("SELECT date, sum(aum_crore) as total_aum FROM aum_by_fund_house GROUP BY date ORDER BY date", conn)
        aum_df['date'] = pd.to_datetime(aum_df['date'])
        ax1 = plt.subplot2grid((3, 2), (1, 0), rowspan=2)
        sns.lineplot(data=aum_df, x='date', y='total_aum', ax=ax1, color='#1f77b4', linewidth=2.5)
        ax1.set_title("Industry AUM Growth (2022-2025)", fontsize=14)
        ax1.set_ylabel("AUM (₹ Crores)")
        ax1.set_xlabel("")
        ax1.tick_params(axis='x', rotation=45)
    except Exception as e:
        print("Page 1 AUM chart error:", e)

    # Bar chart: AUM by fund house (top 10)
    try:
        fh_df = pd.read_sql("SELECT fund_house, sum(aum_crore) as aum FROM aum_by_fund_house WHERE date = (SELECT max(date) FROM aum_by_fund_house) GROUP BY fund_house ORDER BY aum DESC LIMIT 10", conn)
        ax2 = plt.subplot2grid((3, 2), (1, 1), rowspan=2)
        sns.barplot(data=fh_df, x='aum', y='fund_house', ax=ax2, palette='Blues_r')
        ax2.set_title("Top 10 Fund Houses by AUM", fontsize=14)
        ax2.set_xlabel("AUM (₹ Crores)")
        ax2.set_ylabel("")
    except Exception as e:
        print("Page 1 Fund House chart error:", e)

    out_path = os.path.join(OUT_DIR, "Page_1_Industry_Overview.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=150)
    return out_path, fig

# ----------------- PAGE 2: Fund Performance -----------------
def generate_page_2():
    fig = plt.figure(figsize=(16, 9))
    add_bluestock_branding(fig, "PAGE 2: Fund Performance")

    # Scatter plot: Return (X) vs Risk (Y), bubble = AUM
    try:
        perf_df = pd.read_sql("""
            SELECT p.return_3yr_pct, p.std_dev_ann_pct, p.aum_crore, f.category 
            FROM fact_performance p 
            JOIN dim_fund f ON p.amfi_code = f.amfi_code
            WHERE p.return_3yr_pct IS NOT NULL AND p.std_dev_ann_pct IS NOT NULL
        """, conn)
        ax1 = plt.subplot(1, 2, 1)
        sns.scatterplot(data=perf_df, x='return_3yr_pct', y='std_dev_ann_pct', size='aum_crore', hue='category', sizes=(50, 800), alpha=0.7, ax=ax1)
        ax1.set_title("Risk vs Return (3 Yr)", fontsize=14)
        ax1.set_xlabel("Return (3Yr %)")
        ax1.set_ylabel("Risk (Std Dev %)")
        ax1.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize='small', title="Category")
    except Exception as e:
        print("Page 2 Scatter error:", e)

    # Line chart: NAV vs Benchmark (Simulated for visual)
    try:
        nav_df = pd.read_sql("SELECT date, nav FROM fact_nav WHERE amfi_code = 119092 ORDER BY date", conn)
        nav_df['date'] = pd.to_datetime(nav_df['date'])
        
        bench_df = pd.read_sql("SELECT date, close_value as bench_nav FROM benchmark_indices WHERE index_name = 'NIFTY50' ORDER BY date", conn)
        bench_df['date'] = pd.to_datetime(bench_df['date'])
        
        merged = pd.merge(nav_df, bench_df, on='date', how='inner').dropna()
        merged['nav_normalized'] = merged['nav'] / merged['nav'].iloc[0] * 100
        merged['bench_normalized'] = merged['bench_nav'] / merged['bench_nav'].iloc[0] * 100

        ax2 = plt.subplot(1, 2, 2)
        ax2.plot(merged['date'], merged['nav_normalized'], label="Fund NAV", linewidth=2, color='#1f77b4')
        ax2.plot(merged['date'], merged['bench_normalized'], label="Benchmark (NIFTY 50)", linewidth=2, linestyle='--', color='#ff7f0e')
        ax2.set_title("NAV vs Benchmark (Normalized)", fontsize=14)
        ax2.set_ylabel("Growth (Base 100)")
        ax2.tick_params(axis='x', rotation=45)
        ax2.legend()
    except Exception as e:
        print("Page 2 NAV chart error:", e)

    out_path = os.path.join(OUT_DIR, "Page_2_Fund_Performance.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=150)
    return out_path, fig

# ----------------- PAGE 3: Investor Analytics -----------------
def generate_page_3():
    fig = plt.figure(figsize=(16, 9))
    add_bluestock_branding(fig, "PAGE 3: Investor Analytics")

    # Bar: Transaction Amount by State
    try:
        state_df = pd.read_sql("SELECT state, sum(amount_inr) as amount FROM fact_transactions GROUP BY state ORDER BY amount DESC LIMIT 10", conn)
        ax1 = plt.subplot(2, 2, 1)
        sns.barplot(data=state_df, x='amount', y='state', palette='viridis', ax=ax1)
        ax1.set_title("Transaction Vol by State (Top 10)")
        ax1.set_xlabel("Amount (₹)")
        ax1.set_ylabel("")
    except Exception as e:
        print("Page 3 State error:", e)

    # Donut: SIP vs Lumpsum vs Redemption
    try:
        type_df = pd.read_sql("SELECT transaction_type, sum(amount_inr) as amount FROM fact_transactions GROUP BY transaction_type", conn)
        ax2 = plt.subplot(2, 2, 2)
        ax2.pie(type_df['amount'], labels=type_df['transaction_type'], autopct='%1.1f%%', colors=['#2ca02c', '#1f77b4', '#d62728'], wedgeprops=dict(width=0.4))
        ax2.set_title("Transaction Split")
    except Exception as e:
        print("Page 3 Donut error:", e)

    # Bar: Age group vs avg SIP amount
    try:
        age_df = pd.read_sql("SELECT age_group, avg(amount_inr) as avg_amount FROM fact_transactions WHERE transaction_type = 'SIP' GROUP BY age_group ORDER BY age_group", conn)
        ax3 = plt.subplot(2, 2, 3)
        sns.barplot(data=age_df, x='age_group', y='avg_amount', palette='mako', ax=ax3)
        ax3.set_title("Avg SIP Amount by Age Group")
        ax3.set_xlabel("Age Group")
        ax3.set_ylabel("Avg SIP (₹)")
    except Exception as e:
        print("Page 3 Age error:", e)

    # Line: Monthly transaction volume
    try:
        vol_df = pd.read_sql("SELECT substr(transaction_date, 1, 7) as month, sum(amount_inr) as vol FROM fact_transactions GROUP BY month ORDER BY month", conn)
        ax4 = plt.subplot(2, 2, 4)
        sns.lineplot(data=vol_df, x='month', y='vol', marker='o', color='#ff7f0e', ax=ax4)
        ax4.set_title("Monthly Transaction Volume")
        ax4.set_xlabel("Month")
        ax4.set_ylabel("Volume (₹)")
        ax4.tick_params(axis='x', rotation=45)
    except Exception as e:
        print("Page 3 Line error:", e)

    out_path = os.path.join(OUT_DIR, "Page_3_Investor_Analytics.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=150)
    return out_path, fig

# ----------------- PAGE 4: SIP & Market Trends -----------------
def generate_page_4():
    fig = plt.figure(figsize=(16, 9))
    add_bluestock_branding(fig, "PAGE 4: SIP & Market Trends")

    # Heat map: Category inflows by month
    try:
        heat_df = pd.read_sql("SELECT month, category, net_inflow_crore FROM category_inflows", conn)
        if not heat_df.empty:
            pivot_df = heat_df.pivot(index="category", columns="month", values="net_inflow_crore").fillna(0)
            ax1 = plt.subplot(2, 1, 1)
            sns.heatmap(pivot_df, cmap='RdYlGn', ax=ax1, linewidths=.5)
            ax1.set_title("Category Net Inflows Heatmap (₹ Cr)")
            ax1.set_xlabel("Month")
            ax1.set_ylabel("Category")
    except Exception as e:
        print("Page 4 Heatmap error:", e)

    # Bar: Top 5 categories by net inflow FY25
    try:
        top_cat = pd.read_sql("SELECT category, sum(net_inflow_crore) as tot FROM category_inflows GROUP BY category ORDER BY tot DESC LIMIT 5", conn)
        ax2 = plt.subplot(2, 2, 3)
        sns.barplot(data=top_cat, x='tot', y='category', palette='magma', ax=ax2)
        ax2.set_title("Top 5 Categories by Net Inflow")
        ax2.set_xlabel("Net Inflow (₹ Cr)")
        ax2.set_ylabel("")
    except Exception as e:
        print("Page 4 Bar error:", e)

    # KPI box
    try:
        kpi_ax = plt.subplot(2, 2, 4)
        kpi_ax.axis('off')
        kpi_ax.text(0.5, 0.7, "SIP Accounts Growth YoY", fontsize=16, ha='center', color='#555')
        kpi_ax.text(0.5, 0.4, "+18.4%", fontsize=36, fontweight='bold', ha='center', color='#2ca02c')
        kpi_ax.text(0.5, 0.2, "Total Active SIPs: 8.4 Cr", fontsize=14, ha='center', color='#777')
    except Exception as e:
        print("Page 4 KPI error:", e)

    out_path = os.path.join(OUT_DIR, "Page_4_SIP_Trends.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=150)
    return out_path, fig

def main():
    print("Generating Page 1...")
    p1_path, fig1 = generate_page_1()
    print("Generating Page 2...")
    p2_path, fig2 = generate_page_2()
    print("Generating Page 3...")
    p3_path, fig3 = generate_page_3()
    print("Generating Page 4...")
    p4_path, fig4 = generate_page_4()

    pdf_path = os.path.join(OUT_DIR, "Dashboard.pdf")
    print(f"Exporting PDF to {pdf_path}...")
    with PdfPages(pdf_path) as pdf:
        pdf.savefig(fig1)
        pdf.savefig(fig2)
        pdf.savefig(fig3)
        pdf.savefig(fig4)
        
    print("Dashboard mockups successfully created in the 'dashboard' folder.")

if __name__ == '__main__':
    main()
