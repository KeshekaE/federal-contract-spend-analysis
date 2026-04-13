"""
Federal Contract Spend Analysis
Step 1: Pull data from USAspending.gov API
Author: Kesheka Edupuganti
"""

import requests
import pandas as pd
import json
import time
import os
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
BASE_URL = "https://api.usaspending.gov/api/v2"
OUTPUT_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FISCAL_YEAR = 2024  # Change to pull different years

# Top agencies to profile (CGAC codes)
TARGET_AGENCIES = {
    "097": "Department of Defense",
    "075": "Department of Health and Human Services",
    "047": "General Services Administration",
    "089": "Department of Energy",
    "021": "Department of Agriculture",
    "070": "Department of Homeland Security",
}

# NAICS sectors of interest
TARGET_NAICS_PREFIXES = [
    "54",   # Professional, Scientific & Technical Services
    "33",   # Manufacturing
    "23",   # Construction
    "62",   # Health Care & Social Assistance
    "51",   # Information Technology
    "48",   # Transportation
]


# ── Helpers ──────────────────────────────────────────────────────────────────
def safe_get(url, params=None, retries=3, delay=1.5):
    """GET with retry logic."""
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    return None


def safe_post(url, payload, retries=3, delay=1.5):
    """POST with retry logic."""
    for attempt in range(retries):
        try:
            r = requests.post(url, json=payload, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    return None


# ── Pull 1: Agency Spend Summary ─────────────────────────────────────────────
def pull_agency_spend():
    print("\n[1/3] Pulling agency spend summaries...")
    records = []

    for cgac, name in TARGET_AGENCIES.items():
        print(f"  → {name}")
        url = f"{BASE_URL}/agency/{cgac}/budgetary_resources/"
        data = safe_get(url, params={"fiscal_year": FISCAL_YEAR})

        if data and "agency_data_by_year" in data:
            for yr_block in data["agency_data_by_year"]:
                if yr_block.get("fiscal_year") == FISCAL_YEAR:
                    records.append({
                        "cgac_code": cgac,
                        "agency_name": name,
                        "fiscal_year": FISCAL_YEAR,
                        "total_budgetary_resources": yr_block.get("agency_budgetary_resources", 0),
                        "total_obligations": yr_block.get("agency_total_obligated", 0),
                        "total_outlays": yr_block.get("agency_total_outlays", 0),
                    })
        time.sleep(0.5)

    df = pd.DataFrame(records)
    path = os.path.join(OUTPUT_DIR, "agency_spend.csv")
    df.to_csv(path, index=False)
    print(f"  Saved {len(df)} agency records → {path}")
    return df


# ── Pull 2: Contract Awards by NAICS ─────────────────────────────────────────
def pull_naics_awards():
    print("\n[2/3] Pulling contract awards by NAICS...")
    all_records = []

    for prefix in TARGET_NAICS_PREFIXES:
        print(f"  → NAICS prefix {prefix}...")
        payload = {
            "filters": {
                "time_period": [{"start_date": f"{FISCAL_YEAR - 1}-10-01",
                                  "end_date":   f"{FISCAL_YEAR}-09-30"}],
                "award_type_codes": ["A", "B", "C", "D"],  # Contracts only
                "naics_codes": [prefix],
            },
            "fields": [
                "Award ID", "Recipient Name", "Award Amount",
                "NAICS Code", "NAICS Description", "Awarding Agency",
                "Period of Performance Start Date", "Period of Performance Current End Date",
                "Place of Performance State Code",
            ],
            "page": 1,
            "limit": 100,
            "sort": "Award Amount",
            "order": "desc",
        }

        data = safe_post(f"{BASE_URL}/search/spending_by_award/", payload)
        if data and "results" in data:
            for row in data["results"]:
                row["naics_sector_prefix"] = prefix
                all_records.append(row)

        time.sleep(0.8)

    df = pd.DataFrame(all_records)
    path = os.path.join(OUTPUT_DIR, "naics_awards_raw.csv")
    df.to_csv(path, index=False)
    print(f"  Saved {len(df)} award records → {path}")
    return df


# ── Pull 3: Award Size Distribution ──────────────────────────────────────────
def pull_award_distribution():
    print("\n[3/3] Pulling award size distribution...")
    payload = {
        "filters": {
            "time_period": [{"start_date": f"{FISCAL_YEAR - 1}-10-01",
                              "end_date":   f"{FISCAL_YEAR}-09-30"}],
            "award_type_codes": ["A", "B", "C", "D"],
        },
        "category": "awarding_agency",
        "limit": 50,
        "page": 1,
    }

    data = safe_post(f"{BASE_URL}/search/spending_by_category/", payload)
    records = []

    if data and "results" in data:
        for item in data["results"]:
            records.append({
                "agency": item.get("name", ""),
                "amount": item.get("amount", 0),
                "fiscal_year": FISCAL_YEAR,
            })

    df = pd.DataFrame(records)
    path = os.path.join(OUTPUT_DIR, "award_distribution.csv")
    df.to_csv(path, index=False)
    print(f"  Saved {len(df)} distribution records → {path}")
    return df


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"=== USAspending Data Pull — FY{FISCAL_YEAR} ===")
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    agency_df   = pull_agency_spend()
    naics_df    = pull_naics_awards()
    dist_df     = pull_award_distribution()

    print("\n=== Pull complete ===")
    print(f"  Agency records  : {len(agency_df)}")
    print(f"  NAICS awards    : {len(naics_df)}")
    print(f"  Distribution    : {len(dist_df)}")
    print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nAll files saved to: {os.path.abspath(OUTPUT_DIR)}")



import requests
import pandas as pd
import os
import time

DATA_DIR = os.path.join(os.getcwd(), "data")

# Fix 1: Correct Agriculture CGAC code (012, not 021)
print("Fixing Agriculture pull...")
r = requests.get("https://api.usaspending.gov/api/v2/agency/012/budgetary_resources/",
                 params={"fiscal_year": 2024})
if r.status_code == 200:
    data = r.json()
    for yr in data.get("agency_data_by_year", []):
        if yr.get("fiscal_year") == 2024:
            print(f"  Agriculture obligations: ${yr.get('agency_total_obligated',0)/1e9:.1f}B")

# Fix 2: Correct distribution endpoint
print("\nFixing award distribution pull...")
payload = {
    "filters": {
        "time_period": [{"start_date": "2023-10-01", "end_date": "2024-09-30"}],
        "award_type_codes": ["A","B","C","D"]
    },
    "category": "awarding_agency",
    "limit": 50,
    "page": 1
}
r = requests.post("https://api.usaspending.gov/api/v2/search/spending_by_category/awarding_agency/",
                  json=payload)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    results = r.json().get("results", [])
    df = pd.DataFrame([{"agency": x.get("name",""), "amount": x.get("amount",0)} for x in results])
    df["amount_B"] = (df["amount"] / 1e9).round(2)
    df["share_pct"] = (df["amount"] / df["amount"].sum() * 100).round(2)
    df["rank"] = range(1, len(df)+1)
    df.to_csv(os.path.join(DATA_DIR, "award_distribution.csv"), index=False)
    print(f"  Saved {len(df)} distribution records")
    print(df.head())
else:
    print(f"  Error: {r.text[:200]}")
