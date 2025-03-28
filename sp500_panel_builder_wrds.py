# S&P 500 Panel Builder with BoardEx Integration (WRDS JupyterHub)

import wrds
import pandas as pd
import json
from datetime import datetime

# ------------------------------------------
# Step 0: Connect to WRDS
# ------------------------------------------
db = wrds.Connection()

# ------------------------------------------
# Step 1: Load Refinitiv point-in-time S&P500 tickers
# ------------------------------------------
print("Loading Refinitiv S&P500 ticker list...")
with open("/mnt/data/refinitiv_unique_tickers.json", "r") as f:
    refinitiv_ticker_data = json.load(f)
refinitiv_tickers = set([t.upper() for t in refinitiv_ticker_data["tickers"]])

# ------------------------------------------
# Step 2: Get Compustat security identifiers for those tickers
# ------------------------------------------
print("Fetching Compustat identifiers for Refinitiv tickers...")
compustat_ids = db.raw_sql("""
    SELECT gvkey, tic AS ticker
    FROM comp.security
""")

compustat_ids["ticker"] = compustat_ids["ticker"].str.upper()
compustat_ids = compustat_ids[compustat_ids["ticker"].isin(refinitiv_tickers)]

# Add company names from Compustat
company_info = db.raw_sql("SELECT gvkey, conm FROM comp.company")
sp500_firms = compustat_ids.merge(company_info, on="gvkey", how="left")

# ------------------------------------------
# Step 3: Get CRSP-Compustat Linking Table
# ------------------------------------------
print("Fetching CRSP-Compustat link table...")
linktable = db.raw_sql("""
    SELECT gvkey, lpermno AS permno, linkdt, linkenddt, linktype, linkprim
    FROM crsp.ccmxpf_linktable
    WHERE linktype IN ('LU', 'LC') AND linkprim IN ('P', 'C')
""")
sp500_linked = sp500_firms.merge(linktable, on="gvkey", how="left")

# ------------------------------------------
# Step 4: Get CRSP annual price data (year end)
# ------------------------------------------
print("Fetching CRSP annual December data (last 20 years)...")
crsp_data = db.raw_sql("""
    SELECT date, permno, prc, ret, vol, shrout
    FROM crsp.msf
    WHERE EXTRACT(MONTH FROM date) = 12
      AND EXTRACT(DAY FROM date) = 31
      AND date >= '2003-12-31'
""")

crsp_data["fiscal_year"] = pd.to_datetime(crsp_data["date"]).dt.year

# ------------------------------------------
# Step 5: Build annual snapshot panel
# ------------------------------------------
print("Constructing annual snapshots...")
historical_snapshots = crsp_data.merge(sp500_linked, on='permno', how='inner')
historical_snapshots = historical_snapshots[['date', 'permno', 'gvkey', 'ticker', 'conm', 'fiscal_year']]

# ------------------------------------------
# Step 6: Merge BoardEx Data
# ------------------------------------------
print("Fetching BoardEx metadata (boardid)...")
boardex_ids = db.raw_sql("""
    SELECT boardid, ticker, boardname
    FROM boardex.na_wrds_company_profile
""")

historical_snapshots["ticker"] = historical_snapshots["ticker"].str.upper()
boardex_ids["ticker"] = boardex_ids["ticker"].str.upper()
historical_snapshots = historical_snapshots.merge(boardex_ids, on="ticker", how="left")

# ------------------------------------------
# Step 7: Pull BoardEx board composition info
# ------------------------------------------
print("Fetching BoardEx board characteristics...")
boardex_data = db.raw_sql("""
    SELECT boardid, annualreportdate, numberdirectors, genderratio, stdevage
    FROM boardex.na_board_characteristics
    WHERE numberdirectors IS NOT NULL AND genderratio IS NOT NULL
""")

boardex_data = boardex_data[boardex_data["annualreportdate"] != "9000-01-01"]
boardex_data["annualreportdate"] = pd.to_datetime(boardex_data["annualreportdate"], errors="coerce")
boardex_data["fiscal_year"] = boardex_data["annualreportdate"].dt.year
boardex_data["pct_female_directors"] = 1 - boardex_data["genderratio"]
boardex_data["estimated_num_female_directors"] = (boardex_data["numberdirectors"] * boardex_data["pct_female_directors"]).round(2)

# ------------------------------------------
# Step 8: Add Compustat financial ratios
# ------------------------------------------
print("Fetching Compustat financial variables for ratio construction...")
comp_funda = db.raw_sql("""
    SELECT gvkey, datadate, fyear, at, lt, ceq, act, lct, ni, dltt, pstk, csho, prcc_f
    FROM comp.funda
    WHERE datadate >= '2003-01-01' AND indfmt = 'INDL' AND datafmt = 'STD' AND popsrc = 'D' AND consol = 'C'
""")

comp_funda["tobins_q"] = (comp_funda["prcc_f"] * comp_funda["csho"] + comp_funda["at"] - comp_funda["ceq"]) / comp_funda["at"]
comp_funda["liquidity_ratio"] = comp_funda["act"] / comp_funda["lct"]
comp_funda["leverage_ratio"] = comp_funda["dltt"] / comp_funda["at"]
comp_funda["roa"] = comp_funda["ni"] / comp_funda["at"]

comp_funda = comp_funda[["gvkey", "fyear", "tobins_q", "liquidity_ratio", "leverage_ratio", "roa"]]

# ------------------------------------------
# Step 9: Merge everything together
# ------------------------------------------
final_panel = historical_snapshots.merge(
    boardex_data,
    on=["boardid", "fiscal_year"],
    how="left"
)

final_panel = final_panel.merge(
    comp_funda,
    left_on=["gvkey", "fiscal_year"],
    right_on=["gvkey", "fyear"],
    how="left"
).drop(columns="fyear")

# ------------------------------------------
# Step 10: Sanity checks
# ------------------------------------------
print("Sanity checks:")
total_count = len(final_panel)
print(f"Board size coverage: {final_panel['numberdirectors'].notna().sum()} of {total_count}")
print(f"Gender ratio coverage: {final_panel['genderratio'].notna().sum()} of {total_count}")
print(f"Age proxy (stdevage) coverage: {final_panel['stdevage'].notna().sum()} of {total_count}")

# ------------------------------------------
# Step 11: Save
# ------------------------------------------
final_panel.to_csv("sp500_panel_refinitiv_based_20yr.csv", index=False)
print("✅ Saved panel based on Refinitiv S&P500 tickers (20-year horizon)")

# Close WRDS connection
db.close()
