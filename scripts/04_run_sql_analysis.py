"""
Federal Contract Spend Analysis
Step 4: Load cleaned data into SQLite and run SQL analysis
Author: Kesheka Edupuganti
"""

import sqlite3
import pandas as pd
import os
import json

DATA_DIR   = os.path.join(os.getcwd(), "data")
OUTPUT_DIR = os.path.join(os.getcwd(), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
DB_PATH = os.path.join(OUTPUT_DIR, "federal_contracts.db")

def load_to_sqlite():
    conn = sqlite3.connect(DB_PATH)
    tables = {
        "agency_spend":       "agency_spend_clean.csv",
        "naics_awards":       "naics_awards_clean.csv",
        "award_distribution": "award_distribution_clean.csv",
    }
    for table, filename in tables.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            print(f"  WARNING: {filename} not found")
            continue
        df = pd.read_csv(path)
        df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"  Loaded {len(df):,} rows → {table}")
    conn.close()
    print(f"  Database saved → {DB_PATH}")

def run_query(conn, label, sql):
    try:
        df = pd.read_sql_query(sql, conn)
        print(f"\n── {label} ──")
        print(df.to_string(index=False))
        return df
    except Exception as e:
        print(f"  ERROR in '{label}': {e}")
        return pd.DataFrame()

def run_all_analysis():
    conn = sqlite3.connect(DB_PATH)
    results = {}

    results["agency_obligations"] = run_query(conn, "Top Agencies by Obligation", """
        SELECT agency_name,
               ROUND(total_obligations_B, 2)  AS obligations_B,
               ROUND(obligation_rate_pct, 1)  AS obligation_rate_pct,
               CASE WHEN obligation_rate_pct >= 90 THEN 'High'
                    WHEN obligation_rate_pct >= 70 THEN 'Moderate'
                    ELSE 'Low' END AS efficiency
        FROM agency_spend
        ORDER BY total_obligations DESC
    """)

    results["naics_by_sector"] = run_query(conn, "Contract Value by NAICS Sector", """
        SELECT naics_sector,
               COUNT(*)                           AS award_count,
               ROUND(SUM(award_amount)/1e9, 2)   AS total_value_B,
               ROUND(AVG(award_amount)/1e6, 2)   AS avg_award_M
        FROM naics_awards
        GROUP BY naics_sector
        ORDER BY total_value_B DESC
    """)

    results["tier_distribution"] = run_query(conn, "Contract Tier Distribution", """
        SELECT contract_tier,
               COUNT(*)                                                          AS contract_count,
               ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM naics_awards), 1)     AS pct_count,
               ROUND(SUM(award_amount)/1e9, 2)                                  AS total_value_B
        FROM naics_awards
        GROUP BY contract_tier
        ORDER BY MIN(award_amount) DESC
    """)

    results["spend_concentration"] = run_query(conn, "Top Agencies by Spend", """
        SELECT rank, agency,
               ROUND(amount_B, 2)  AS total_B,
               ROUND(share_pct, 2) AS share_pct
        FROM award_distribution
        ORDER BY rank
        LIMIT 10
    """)

    # KPIs
    kpi_queries = {
        "total_spend_B":       "SELECT ROUND(SUM(award_amount)/1e9,1) AS v FROM naics_awards",
        "unique_contractors":  "SELECT COUNT(DISTINCT recipient_name) AS v FROM naics_awards",
        "avg_contract_M":      "SELECT ROUND(AVG(award_amount)/1e6,2) AS v FROM naics_awards",
        "tier_a_pct_of_spend": """
            SELECT ROUND(
                SUM(CASE WHEN contract_tier='A — Large (≥$10M)' THEN award_amount ELSE 0 END)
                / SUM(award_amount)*100, 1) AS v
            FROM naics_awards
        """,
    }
    kpis = {}
    print("\n── KPI Summary ──")
    for key, sql in kpi_queries.items():
        try:
            val = pd.read_sql_query(sql, conn).iloc[0, 0]
            kpis[key] = val
            print(f"  {key}: {val}")
        except Exception as e:
            print(f"  ERROR {key}: {e}")

    for key, val in results.items():
        if isinstance(val, pd.DataFrame) and not val.empty:
            val.to_csv(os.path.join(OUTPUT_DIR, f"{key}.csv"), index=False)

    with open(os.path.join(OUTPUT_DIR, "kpis.json"), "w") as f:
        json.dump({k: float(v) if v is not None else None for k, v in kpis.items()}, f, indent=2)

    print(f"\n  All results exported → {OUTPUT_DIR}")
    conn.close()

# ── Run ──
print("=== SQL Analysis Pipeline ===")
print("Loading data into SQLite...")
load_to_sqlite()
print("\nRunning analysis queries...")
run_all_analysis()
print("\n=== Analysis complete ===")
