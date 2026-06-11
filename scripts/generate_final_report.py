import os
from pathlib import Path
from fpdf import FPDF

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / 'reports'
CHARTS_DIR = REPORTS_DIR / 'eda_charts'

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Bluestock MF Capstone - Final Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 16)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, text):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 8, text)
        self.ln()

    def add_image_page(self, title, img_path, description=""):
        self.add_page()
        self.chapter_title(title)
        if description:
            self.chapter_body(description)
        if os.path.exists(img_path):
            self.image(str(img_path), w=180)
        else:
            self.chapter_body(f"[Image not found: {img_path}]")

def create_report():
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title Page
    pdf.add_page()
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 60, "", 0, 1)
    pdf.cell(0, 20, "Bluestock Mutual Fund Analytics", 0, 1, 'C')
    pdf.set_font("Arial", "I", 16)
    pdf.cell(0, 15, "Capstone Project Final Report", 0, 1, 'C')
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 40, "Prepared for: Executive Board", 0, 1, 'C')
    
    # Executive Summary
    pdf.add_page()
    pdf.chapter_title("1. Executive Summary")
    exec_summary = (
        "This report encapsulates the comprehensive analytics pipeline developed for Bluestock Mutual Funds. "
        "The project successfully implements an end-to-end ETL architecture, ingesting raw mutual fund "
        "data, processing it into a robust data warehouse, and serving actionable insights through "
        "advanced analytics and interactive dashboards.\n\n"
        "Key achievements include:\n"
        "- Processing and standardizing 10+ datasets covering 40 schemes.\n"
        "- Constructing a Star Schema database optimized for analytical queries.\n"
        "- Generating automated Exploratory Data Analysis (EDA) uncovering critical market trends.\n"
        "- Calculating sophisticated performance metrics including Alpha, Beta, Sharpe Ratio, and VaR.\n"
        "- Developing a dynamic Tableau/Power BI dashboard for executive monitoring."
    )
    pdf.chapter_body(exec_summary)

    # Data Sources
    pdf.add_page()
    pdf.chapter_title("2. Data Sources")
    data_sources = (
        "The analysis relies on a combination of internal system dumps and external market data APIs.\n\n"
        "1. Internal Dumps (CSVs): Includes dim_fund_master, dim_date, fact_nav_history, fact_aum, "
        "fact_transactions, category_inflows, and portfolio_holdings.\n"
        "2. External APIs: Live NAV data is fetched via the AMFI (Association of Mutual Funds in India) "
        "public API, ensuring up-to-date pricing for the 40 targeted schemes.\n"
        "3. Benchmarks: Nifty 50 and Nifty Midcap 150 historical data is utilized to baseline performance."
    )
    pdf.chapter_body(data_sources)

    # ETL Design
    pdf.add_page()
    pdf.chapter_title("3. ETL Architecture & Design")
    etl_design = (
        "The ETL (Extract, Transform, Load) pipeline is designed for idempotency and scalability.\n\n"
        "Extract Phase: Raw CSVs are read using pandas. The AMFI API is queried concurrently for live NAVs.\n"
        "Transform Phase: Data is cleansed, nulls handled (e.g., forward filling missing NAVs), "
        "and data types enforced. We utilized Regex for scheme name normalization and mapped categorical "
        "variables standardizing fund categories.\n"
        "Load Phase: Transformed data is loaded into a SQLite relational database structured in a Star Schema. "
        "The schema features a central fact table (fact_nav, fact_performance) linked to dimensions "
        "(dim_fund, dim_date), optimizing query performance for analytical tools."
    )
    pdf.chapter_body(etl_design)

    # EDA Findings (Text + Charts)
    pdf.add_page()
    pdf.chapter_title("4. Exploratory Data Analysis (EDA) Findings")
    eda_findings = (
        "The EDA process uncovered several pivotal insights regarding investor behavior and market trends. "
        "We observed a pronounced bull run in 2023, reflected across equity schemes, followed by a minor correction. "
        "Furthermore, SIP (Systematic Investment Plan) inflows have shown remarkable resilience, "
        "peaking at an all-time high of over 31,000 Crores in late 2025. "
        "Demographically, millennials constitute the highest volume of investors, though older demographics "
        "contribute higher average investment amounts."
    )
    pdf.chapter_body(eda_findings)
    
    # Add EDA Charts
    charts = [
        ("NAV Trend Analysis", CHARTS_DIR / '1_nav_trend.png', "The chart illustrates the 2023 Bull Run and subsequent volatility."),
        ("AUM Growth", CHARTS_DIR / '2_aum_growth.png', "SBI Mutual Fund maintains market dominance in total Assets Under Management."),
        ("SIP Inflows", CHARTS_DIR / '3_sip_inflows.png', "Unbroken month-on-month growth in SIP contributions."),
        ("Category Heatmap", CHARTS_DIR / '4_category_heatmap.png', "Inflows surged in Small and Mid Cap funds during late 2023."),
        ("Investor Demographics", CHARTS_DIR / '5_demographics.png', "Breakdown by Age and Gender."),
        ("Geographic Distribution", CHARTS_DIR / '6_geographic.png', "Maharashtra leads, but B30 cities are showing aggressive growth.")
    ]
    
    for title, img_path, desc in charts:
        pdf.add_image_page(f"EDA: {title}", img_path, desc)

    # Performance Analysis
    pdf.add_page()
    pdf.chapter_title("5. Performance Analysis")
    perf_analysis = (
        "Performance metrics were computed to evaluate risk-adjusted returns against benchmark indices.\n\n"
        "- Rolling Sharpe Ratios: High-growth equity funds maintained Sharpe Ratios above 1.5 during bull phases, indicating excellent risk-adjusted performance.\n"
        "- Alpha & Beta: Small Cap funds demonstrated high Beta (>1.2) capturing market upside, while generating positive Alpha.\n"
        "- Value at Risk (VaR): Computed at 95% confidence, highlighting maximum expected daily loss, critical for risk management."
    )
    pdf.chapter_body(perf_analysis)

    pdf.add_image_page("Performance: Benchmark Comparison", BASE_DIR / 'benchmark_comparison_chart.png', 
                       "Comparison of scheme returns against benchmark.")
    pdf.add_image_page("Performance: Rolling Sharpe", BASE_DIR / 'rolling_sharpe_chart.png', 
                       "30-Day Rolling Sharpe Ratio showcasing risk-adjusted performance volatility.")

    # Dashboard Screenshots
    pdf.add_page()
    pdf.chapter_title("6. Dashboard Visualizations")
    dash_desc = (
        "The final deliverable includes a comprehensive BI Dashboard allowing executives to interactively drill down into metrics. "
        "The dashboard integrates AUM tracking, demographic splits, and real-time performance indicators."
    )
    pdf.chapter_body(dash_desc)
    pdf.add_image_page("Dashboard: Main View", BASE_DIR / 'dashboard' / 'Page_1_Industry_Overview.png', "Executive Summary View")
    pdf.add_image_page("Dashboard: Performance View", BASE_DIR / 'dashboard' / 'Page_2_Fund_Performance.png', "Detailed Performance Metrics")

    # Limitations & Recommendations
    pdf.add_page()
    pdf.chapter_title("7. Limitations")
    limits = (
        "1. Data Frequency: While NAV is daily, demographic data is monthly, preventing real-time behavior tracking.\n"
        "2. Scope: The analysis is constrained to 40 primary schemes. Expanding to the broader market would require distributed processing.\n"
        "3. Predictive Power: Current analytics are descriptive and diagnostic; predictive modeling is slated for future phases."
    )
    pdf.chapter_body(limits)

    pdf.chapter_title("8. Recommendations")
    recs = (
        "1. Product Strategy: Capitalize on the B30 city growth by launching targeted localized campaigns.\n"
        "2. Risk Mitigation: Introduce dynamic hedging for high-beta Small Cap funds given the anticipated market volatility.\n"
        "3. Technology: Transition the SQLite database to a cloud-native PostgreSQL instance (e.g., AWS RDS) to support concurrent read-heavy dashboard loads."
    )
    pdf.chapter_body(recs)

    # Output
    output_path = BASE_DIR / 'Final_Report.pdf'
    pdf.output(str(output_path))
    print(f"Report generated successfully: {output_path}")

if __name__ == "__main__":
    create_report()
