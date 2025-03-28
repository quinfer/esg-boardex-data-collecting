# director_diversity_aggregator.py

import wrds
import pandas as pd
from datetime import datetime

# Load existing S&P500 panel with companyid and fiscal_year
panel = pd.read_csv("sp500_panel_compustat_boardex_refinitiv.csv")
key_pairs = panel[["companyid", "fiscal_year"]].dropna().drop_duplicates()

# Connect to WRDS
db = wrds.Connection()

# Upload the relevant company-year pairs as a temporary SQL table
print("Uploading filter of companyid and fiscal_year to WRDS...")
db.bulk_insert("temp_keys", key_pairs)

# Query only relevant directors from BoardEx using the uploaded filter
print("Querying filtered director profiles...")
directors = db.raw_sql("""
    SELECT d.directorid, d.gender, d.dob AS dateofbirth,
           e.companyid, e.datestartrole AS emp_start, e.dateendrole AS emp_end
    FROM boardex.na_dir_profile_details d
    JOIN boardex.na_dir_profile_emp e ON d.directorid = e.directorid
    JOIN temp_keys k ON e.companyid = k.companyid AND EXTRACT(YEAR FROM e.datestartrole) = k.fiscal_year
    WHERE d.gender IS NOT NULL AND d.dob IS NOT NULL AND e.datestartrole IS NOT NULL
""")
print(f"✅ Retrieved {len(directors):,} director records")

# Convert dates
directors["dateofbirth"] = pd.to_datetime(directors["dateofbirth"], errors="coerce")
directors["emp_start"] = pd.to_datetime(directors["emp_start"], errors="coerce")
directors["emp_end"] = pd.to_datetime(directors["emp_end"], errors="coerce")

# Compute age at start
directors["age_at_start"] = (directors["emp_start"] - directors["dateofbirth"]).dt.days // 365
directors["fiscal_year"] = directors["emp_start"].dt.year

# Aggregate to company-year level
agg = (
    directors.groupby(["companyid", "fiscal_year"])
    .agg(
        num_directors=("directorid", "nunique"),
        pct_female=("gender", lambda x: (x.str.upper() == "FEMALE").mean()),
        num_female=("gender", lambda x: (x.str.upper() == "FEMALE").sum()),
        avg_age=("age_at_start", "mean"),
        stdev_age=("age_at_start", "std"),
    )
    .reset_index()
)

# Save both director-level and aggregated datasets
directors.to_csv("director_level_data.csv", index=False)
agg.to_csv("boardex_director_diversity_by_company_year.csv", index=False)
print("✅ Files saved: director_level_data.csv, boardex_director_diversity_by_company_year.csv")

# Cleanup temp table
db.execute_sql("DROP TABLE IF EXISTS temp_keys;")
db.close()
