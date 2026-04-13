"""
Federal Contract Spend Analysis
Step 2: Clean and validate raw data
Author: Kesheka Edupuganti
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

DATA_DIR   = os.path.join(os.getcwd(), "data")
OUTPUT_DIR = DATA_DIR

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def make_serializable(obj):
    if isinstance(obj, np.integer): return int(obj)
    if isinstance(obj, np.floating): return float(obj)
    if isinstance(obj, np.ndarray): return obj.tolist()
    return obj

def clean_agency_spend():
    log("Cleaning agency_spend.csv...")
    df = pd.read_csv(os.path.join(DATA_DIR, "agency_spend.csv"))
    for col in ["total_budgetary_resources", "total_obligations", "total_outlays"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["obligation_rate_pct"] = (
        (df["total_obligations"] / df["total_budgetary_resources"])
        .replace([np.inf, -np.inf], 0).fillna(0).round(4) * 100
    )
    for col in ["total_budgetary_resources", "total_obligations", "total_outlays"]:
        df[f"{col}_B"] = (df[col] / 1e9).round(2)
    df = df[df["agency_name"].notna() & (df["agency_name"] != "")]
    df.to_csv(os.path.join(OUTPUT_DIR, "agency_spend_clean.csv"), index=False)
    log(f"  Saved {len(df)} agency rows")
    return df

def clean_naics_awards():
    log("Cleaning naics_awards_raw.csv...")
    df = pd.read_csv(os.path.join(DATA_DIR, "naics_awards_raw.csv"))
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    df["award_amount"] = pd.to_numeric(df["award_amount"], errors="coerce").fillna(0)
    df = df[df["award_amount"] > 0]
    df = df.drop_duplicates(subset=["award_id"])
    df["naics_code"] = df["naics_code"].astype(str).str.strip()
    df["naics_sector"] = df["naics_code"].str[:2]
    df["state_code"] = df["place_of_performance_state_code"].astype(str).str.upper().str.strip()
    df.loc[df["state_code"].str.len() != 2, "state_code"] = "UNKNOWN"
    def tier(amount):
        if amount >= 10_000_000:  return "A — Large (≥$10M)"
        elif amount >= 1_000_000: return "B — Mid ($1M–$10M)"
        elif amount >= 100_000:   return "C — Small ($100K–$1M)"
        else:                     return "D — Micro (<$100K)"
    df["contract_tier"] = df["award_amount"].apply(tier)
    for col in ["period_of_performance_start_date", "period_of_performance_current_end_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    if all(c in df.columns for c in ["period_of_performance_start_date", "period_of_performance_current_end_date"]):
        df["contract_duration_days"] = (
            df["period_of_performance_current_end_date"] - df["period_of_performance_start_date"]
        ).dt.days
    df.to_csv(os.path.join(OUTPUT_DIR, "naics_awards_clean.csv"), index=False)
    log(f"  Saved {len(df)} award rows")
    return df

def clean_award_distribution():
    log("Cleaning award_distribution.csv...")
    df = pd.read_csv(os.path.join(DATA_DIR, "award_distribution.csv"))
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["amount_B"] = (df["amount"] / 1e9).round(2)
    df["share_pct"] = (df["amount"] / df["amount"].sum() * 100).round(2)
    df = df.sort_values("amount", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    df.to_csv(os.path.join(OUTPUT_DIR, "award_distribution_clean.csv"), index=False)
    log(f"  Saved {len(df)} distribution rows")
    return df

# ── Run all cleaning ──
agency_df = clean_agency_spend()
naics_df  = clean_naics_awards()
dist_df   = clean_award_distribution()

# ── Summary stats ──
summary = {
    "generated_at": datetime.now().isoformat(),
    "agency_spend": {
        "total_agencies": int(len(agency_df)),
        "total_obligations_B": round(float(agency_df["total_obligations_B"].sum()), 2),
        "avg_obligation_rate_pct": round(float(agency_df["obligation_rate_pct"].mean()), 2),
        "top_agency_by_obligation": agency_df.sort_values("total_obligations", ascending=False).iloc[0]["agency_name"],
    },
    "naics_awards": {
        "total_awards": int(len(naics_df)),
        "total_value_B": round(float(naics_df["award_amount"].sum() / 1e9), 2),
        "tier_distribution": {str(k): int(v) for k, v in naics_df["contract_tier"].value_counts().items()},
    },
    "award_distribution": {
        "total_agencies_ranked": int(len(dist_df)),
        "top_3_agencies": dist_df.head(3)["agency"].tolist(),
        "top_3_share_pct": round(float(dist_df.head(3)["share_pct"].sum()), 2),
    },
}

out = os.path.join(OUTPUT_DIR, "summary_stats.json")
with open(out, "w") as f:
    json.dump(summary, f, indent=2, default=make_serializable)

print("\n=== Cleaning complete ===")
print(json.dumps(summary, indent=2, default=make_serializable))
