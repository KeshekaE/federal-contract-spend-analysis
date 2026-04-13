# Federal Contract Spend Analysis

A full-pipeline analysis of U.S. federal contracting data using the USAspending.gov public API — built as a portfolio project by Kesheka Edupuganti, Data Analyst & BI Specialist.

## Project Overview
Analyzes FY2024 federal contract spend across agencies, industries, and contractor tiers — answering three core business questions:
- Which federal agencies are spending the most, and how efficiently?
- Which industries (NAICS codes) are capturing the most contract value?
- What does the contractor landscape look like by size tier?

## Stack
Python · SQL (SQLite) · Jupyter Notebook · Tableau Public

## Repository Structure
federal-contract-spend-analysis/
│
├── scripts/
│   ├── 01_pull_data.py           # Pulls data from USAspending.gov API
│   ├── 02_clean_data.py          # Cleans, validates, engineers features
│   ├── 03_analysis_queries.sql   # 12 SQL queries across spend, NAICS, tiers
│   └── 04_run_sql_analysis.py    # Loads into SQLite, exports results
│
├── notebook/
│   └── Federal_Contract_Analysis.ipynb  # Full pipeline in Jupyter
│
├── output/
│   ├── agency_obligations.csv    # Agency spend + efficiency rankings
│   ├── naics_by_sector.csv       # Contract value by industry
│   ├── spend_concentration.csv   # Top 10 agencies by total award value
│   └── tier_distribution.csv    # A/B/C/D contractor tier breakdown
│
├── data/
│   └── README.md                 # Data sourcing instructions
│
└── docs/
└── README_FederalContractAnalysis.docx  # Full project write-up

## How to Run

**Step 1: Install dependencies**
pip install requests pandas numpy

**Step 2: Pull data from USAspending API**
python scripts/01_pull_data.py

**Step 3: Clean and validate**
python scripts/02_clean_data.py

**Step 4: Run SQL analysis**
python scripts/04_run_sql_analysis.py

Output CSVs will be saved to `/output/` — ready for Tableau or Power BI.

## Pipeline Architecture

| Script | Stage | Output |
|--------|-------|--------|
| 01_pull_data.py | Pull | 3 raw CSVs from USAspending API |
| 02_clean_data.py | Clean | Validated CSVs with engineered features |
| 03_analysis_queries.sql | Analyze | 12 SQL queries (reference file) |
| 04_run_sql_analysis.py | Load + Run | SQLite DB + result CSVs |

## Key Engineering Decisions

**Contractor Tier Segmentation**
Awards classified into four tiers by dollar value:

| Tier | Award Size | Profile |
|------|-----------|---------|
| A — Large | ≥$10M | Strategic partners, major primes |
| B — Mid | $1M–$10M | Established contractors |
| C — Small | $100K–$1M | Small business targets |
| D — Micro | <$100K | Sole source / simplified acquisition |

**Obligation Rate Analysis**
Calculates the share of budgetary resources actually committed per agency — surfaces efficiency gaps relevant to both performance analysis and business development targeting.

**NAICS Sector Profiling**
Six 2-digit NAICS prefixes analyzed: Professional Services (54), Manufacturing (33), Construction (23), Healthcare (62), Information Technology (51), and Transportation (48).

## Key Findings (FY2024)

- **Department of Defense** accounts for **60% ($446B)** of all federal contract spend
- **HHS leads on budget efficiency** at 87.9% obligation rate
- **235 unique contractors** across 595 large awards totaling **$1.5T**
- **Department of Veterans Affairs** ranks #2 at $66.88B (9% market share)
- **Top 3 agencies** (DoD, VA, DoE) control **75%** of total contract spend

## Notes on Data & Compliance
- All data sourced via the **USAspending.gov public API** under the DATA Act
- No bulk downloads used — fully API-based pipeline
- No authentication or API key required
- Data is U.S. government public domain

## Dashboard
[View live on Tableau Public →](https://public.tableau.com/views/FederalContractSpendAnalysisFY2024/Dashboard1)

## Portfolio
[Portfolio Link →](https://keportfolio.vercel.app)

## Author
**Kesheka Edupuganti**  
Data Analyst & BI Specialist | Loma Linda, CA  
ekesheka1010@gmail.com  
[LinkedIn](https://www.linkedin.com/in/kesheka-edupuganti-b53a96293/)
