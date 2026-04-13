-- ============================================================
-- Federal Contract Spend Analysis — SQL Analysis Queries
-- Author: Kesheka Edupuganti
-- Database: SQLite (load CSVs via DB Browser or Python + sqlite3)
-- ============================================================
-- HOW TO USE:
--   Option A: DB Browser for SQLite (free GUI, import CSVs as tables)
--   Option B: Run via Python:
--     import sqlite3, pandas as pd
--     conn = sqlite3.connect(':memory:')
--     pd.read_csv('data/agency_spend_clean.csv').to_sql('agency_spend', conn, index=False)
--     pd.read_csv('data/naics_awards_clean.csv').to_sql('naics_awards', conn, index=False)
--     pd.read_csv('data/award_distribution_clean.csv').to_sql('award_distribution', conn, index=False)
-- ============================================================


-- ── SECTION 1: Agency Spend Analysis ─────────────────────────────────────────

-- Q1: Which agencies have the highest total obligations?
SELECT
    agency_name,
    ROUND(total_obligations_B, 2)          AS obligations_B,
    ROUND(total_budgetary_resources_B, 2)  AS budget_B,
    ROUND(obligation_rate_pct, 1)          AS obligation_rate_pct
FROM agency_spend
ORDER BY total_obligations DESC
LIMIT 10;


-- Q2: Obligation efficiency — which agencies spend the highest share of their budget?
SELECT
    agency_name,
    ROUND(obligation_rate_pct, 1)  AS obligation_rate_pct,
    CASE
        WHEN obligation_rate_pct >= 90 THEN 'High Efficiency'
        WHEN obligation_rate_pct >= 70 THEN 'Moderate'
        ELSE 'Low Efficiency'
    END AS efficiency_tier
FROM agency_spend
ORDER BY obligation_rate_pct DESC;


-- Q3: Gap between obligations and outlays (unspent committed funds)
SELECT
    agency_name,
    ROUND(total_obligations_B - total_outlays_B, 2) AS unspent_obligations_B,
    ROUND(total_obligations_B, 2)                   AS total_obligations_B
FROM agency_spend
ORDER BY unspent_obligations_B DESC;


-- ── SECTION 2: NAICS / Industry Trends ───────────────────────────────────────

-- Q4: Total contract value by NAICS sector
SELECT
    naics_sector,
    COUNT(*)                                        AS award_count,
    ROUND(SUM(award_amount) / 1e9, 2)              AS total_value_B,
    ROUND(AVG(award_amount) / 1e6, 2)              AS avg_award_M,
    ROUND(MAX(award_amount) / 1e6, 2)              AS max_award_M
FROM naics_awards
GROUP BY naics_sector
ORDER BY total_value_B DESC;


-- Q5: Top 10 recipients by total award value
SELECT
    recipient_name,
    COUNT(*)                                        AS contract_count,
    ROUND(SUM(award_amount) / 1e6, 2)              AS total_value_M,
    GROUP_CONCAT(DISTINCT naics_sector)             AS sectors_active_in
FROM naics_awards
GROUP BY recipient_name
ORDER BY total_value_M DESC
LIMIT 10;


-- Q6: NAICS sector activity by state
SELECT
    state_code,
    naics_sector,
    COUNT(*)                               AS award_count,
    ROUND(SUM(award_amount) / 1e6, 2)     AS total_M
FROM naics_awards
WHERE state_code != 'UNKNOWN'
GROUP BY state_code, naics_sector
ORDER BY total_M DESC
LIMIT 30;


-- Q7: Contract duration analysis by sector
SELECT
    naics_sector,
    ROUND(AVG(contract_duration_days), 0)   AS avg_duration_days,
    ROUND(MIN(contract_duration_days), 0)   AS min_duration_days,
    ROUND(MAX(contract_duration_days), 0)   AS max_duration_days
FROM naics_awards
WHERE contract_duration_days IS NOT NULL
  AND contract_duration_days > 0
GROUP BY naics_sector
ORDER BY avg_duration_days DESC;


-- ── SECTION 3: Contractor Tier Segmentation ───────────────────────────────────

-- Q8: Distribution of contracts across A/B/C/D tiers
SELECT
    contract_tier,
    COUNT(*)                                AS contract_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct_of_total,
    ROUND(SUM(award_amount) / 1e9, 2)      AS total_value_B,
    ROUND(AVG(award_amount) / 1e6, 2)      AS avg_award_M
FROM naics_awards
GROUP BY contract_tier
ORDER BY MIN(award_amount) DESC;


-- Q9: Tier breakdown by awarding agency
SELECT
    awarding_agency,
    contract_tier,
    COUNT(*)                                AS award_count,
    ROUND(SUM(award_amount) / 1e6, 2)      AS total_M
FROM naics_awards
GROUP BY awarding_agency, contract_tier
ORDER BY awarding_agency, MIN(award_amount) DESC;


-- Q10: "Tier A" contractors — who are the major players?
SELECT
    recipient_name,
    naics_sector,
    awarding_agency,
    ROUND(award_amount / 1e6, 2)            AS award_M,
    contract_duration_days
FROM naics_awards
WHERE contract_tier = 'A — Large (≥$10M)'
ORDER BY award_amount DESC
LIMIT 20;


-- ── SECTION 4: Award Size Distribution ───────────────────────────────────────

-- Q11: Top agencies by total award value (from distribution pull)
SELECT
    rank,
    agency,
    ROUND(amount_B, 2)     AS total_B,
    ROUND(share_pct, 2)    AS market_share_pct
FROM award_distribution
ORDER BY rank
LIMIT 15;


-- Q12: Cumulative spend concentration (how concentrated is federal spending?)
SELECT
    agency,
    ROUND(amount_B, 2)                          AS total_B,
    ROUND(share_pct, 2)                         AS share_pct,
    ROUND(SUM(share_pct) OVER (
        ORDER BY amount DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2)                                       AS cumulative_share_pct
FROM award_distribution
LIMIT 20;


-- ── SECTION 5: Key Insight Queries (Dashboard KPIs) ──────────────────────────

-- KPI 1: Total federal contract spend analyzed
SELECT ROUND(SUM(award_amount) / 1e9, 1) AS total_spend_B FROM naics_awards;

-- KPI 2: Number of unique contractors
SELECT COUNT(DISTINCT recipient_name) AS unique_contractors FROM naics_awards;

-- KPI 3: Average contract size
SELECT ROUND(AVG(award_amount) / 1e6, 2) AS avg_contract_M FROM naics_awards;

-- KPI 4: Most active sector
SELECT naics_sector, COUNT(*) AS awards
FROM naics_awards
GROUP BY naics_sector
ORDER BY awards DESC
LIMIT 1;

-- KPI 5: Tier A share of total spend
SELECT
    ROUND(
        SUM(CASE WHEN contract_tier = 'A — Large (≥$10M)' THEN award_amount ELSE 0 END)
        / SUM(award_amount) * 100, 1
    ) AS tier_a_pct_of_spend
FROM naics_awards;
