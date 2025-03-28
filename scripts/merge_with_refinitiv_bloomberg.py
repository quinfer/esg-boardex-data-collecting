import pandas as pd
import json

# Load all three datasets
bloomberg = pd.read_excel("data/Bloomberg_unbalanced_2025.xlsx")
refinitiv = pd.read_excel("data/Refinitiv_Unbalanced_2025.xlsx")
final_panel = pd.read_csv("data/sp500_panel_with_diversity.csv")

# Prepare ticker and fiscal year columns for each dataset
bloomberg["ticker_clean"] = bloomberg["Company"].str.extract(r"^([A-Z]+)")
refinitiv["ticker_clean"] = refinitiv["Instrument"].str.extract(r"^([A-Z]+)")
final_panel["ticker_clean"] = final_panel["ticker"].str.upper()

bloomberg["fiscal_year"] = bloomberg["Dates"].astype(int)
refinitiv["fiscal_year"] = refinitiv["Year"]

# Function to identify duplicates in a dataset
def find_duplicates(df, name):
    # Count occurrences of each company-year combination
    counts = df.groupby(["ticker_clean", "fiscal_year"]).size().reset_index(name="count")
    
    # Filter to find duplicates (count > 1)
    duplicates = counts[counts["count"] > 1]
    
    if len(duplicates) > 0:
        print(f"\n{name} dataset has {len(duplicates)} company-years with duplicates:")
        print(duplicates.head(20) if len(duplicates) > 20 else duplicates)
        
        # Get detailed records for each duplicate
        dupe_records = pd.DataFrame()
        for _, row in duplicates.iterrows():
            ticker = row["ticker_clean"]
            year = row["fiscal_year"]
            matches = df[(df["ticker_clean"] == ticker) & (df["fiscal_year"] == year)]
            dupe_records = pd.concat([dupe_records, matches])
        
        # Save duplicates to data/ folder
        dupe_records.to_csv(f"data/{name.lower()}_duplicates.csv", index=False)
        print(f"Full duplicates saved to data/{name.lower()}_duplicates.csv")
    else:
        print(f"\n{name} dataset has no duplicates.")
    
    return duplicates

# Find duplicates in each dataset
refinitiv_dupes = find_duplicates(refinitiv, "Refinitiv")
bloomberg_dupes = find_duplicates(bloomberg, "Bloomberg")
panel_dupes = find_duplicates(final_panel, "Panel")

# Create a function to deduplicate a dataset
def deduplicate(df, name):
    before_count = len(df)
    
    # Option 1: Keep first occurrence
    df_deduped = df.drop_duplicates(subset=["ticker_clean", "fiscal_year"], keep="first")
    
    after_count = len(df_deduped)
    if before_count > after_count:
        print(f"\nDeduplicated {name} dataset: removed {before_count - after_count} duplicate rows")
        # Save deduplicated dataset to data/ folder
        if name == "Refinitiv":
            df_deduped.to_csv("data/refinitiv_deduplicated.csv", index=False)
        elif name == "Bloomberg":
            df_deduped.to_excel("data/bloomberg_deduplicated.xlsx", index=False)
        else:
            df_deduped.to_csv("data/panel_deduplicated.csv", index=False)
    
    return df_deduped

# Deduplicate each dataset if duplicates were found
if len(refinitiv_dupes) > 0:
    refinitiv_clean = deduplicate(refinitiv, "Refinitiv")
else:
    refinitiv_clean = refinitiv

if len(bloomberg_dupes) > 0:
    bloomberg_clean = deduplicate(bloomberg, "Bloomberg")
else:
    bloomberg_clean = bloomberg

if len(panel_dupes) > 0:
    panel_clean = deduplicate(final_panel, "Panel")
else:
    panel_clean = final_panel

# Report on merge keys after deduplication
print("\nAfter deduplication:")
print(f"Refinitiv: {refinitiv_clean['ticker_clean'].nunique()} unique tickers, {refinitiv_clean['fiscal_year'].nunique()} years")
print(f"Bloomberg: {bloomberg_clean['ticker_clean'].nunique()} unique tickers, {bloomberg_clean['fiscal_year'].nunique()} years")
print(f"Panel: {panel_clean['ticker_clean'].nunique()} unique tickers, {panel_clean['fiscal_year'].nunique()} years")

# Check for shared tickers between datasets
refinitiv_tickers = set(refinitiv_clean["ticker_clean"].unique())
bloomberg_tickers = set(bloomberg_clean["ticker_clean"].unique())
panel_tickers = set(panel_clean["ticker_clean"].unique())

print(f"\nTicker overlap analysis:")
print(f"Refinitiv & Bloomberg: {len(refinitiv_tickers.intersection(bloomberg_tickers))} shared tickers")
print(f"Refinitiv & Panel: {len(refinitiv_tickers.intersection(panel_tickers))} shared tickers")
print(f"Bloomberg & Panel: {len(bloomberg_tickers.intersection(panel_tickers))} shared tickers")
print(f"All three datasets: {len(refinitiv_tickers.intersection(bloomberg_tickers, panel_tickers))} shared tickers")

# Before merging, prefix all columns in each dataset
def prefix_columns(df, prefix, exclude=None):
    """Add prefix to all columns except those in exclude list"""
    if exclude is None:
        exclude = []
    
    rename_dict = {col: f"{prefix}_{col}" for col in df.columns if col not in exclude}
    return df.rename(columns=rename_dict)

# Keep merge keys unprefixed
merge_keys = ["ticker_clean", "fiscal_year"]

# Apply prefixes to each dataset
refinitiv_prefixed = prefix_columns(refinitiv_clean, "ref", exclude=merge_keys)
bloomberg_prefixed = prefix_columns(bloomberg_clean, "bbg", exclude=merge_keys)
panel_prefixed = prefix_columns(panel_clean, "wrds", exclude=merge_keys)  # Changed to WRDS

# Now perform the merges (no need for suffixes)
master_clean = refinitiv_prefixed.copy()
master_clean = pd.merge(
    master_clean, 
    bloomberg_prefixed,
    on=merge_keys, 
    how="left"
)
master_clean = pd.merge(
    master_clean,
    panel_prefixed,
    on=merge_keys,
    how="left"
)

# Check merge results
bloomberg_cols = [col for col in master_clean.columns if col.endswith("_bloomberg")]
panel_cols = [col for col in master_clean.columns if col.endswith("_panel")]

missing_bloomberg = master_clean[bloomberg_cols].isna().all(axis=1).sum() if bloomberg_cols else len(master_clean)
missing_panel = master_clean[panel_cols].isna().all(axis=1).sum() if panel_cols else len(master_clean)

print(f"\nTest merge results:")
print(f"Rows in master panel: {len(master_clean)}")
print(f"Rows missing Bloomberg data: {missing_bloomberg} ({missing_bloomberg/len(master_clean)*100:.1f}%)")
print(f"Rows missing Panel data: {missing_panel} ({missing_panel/len(master_clean)*100:.1f}%)")

# Save the master panel with deduplicated data
master_clean.to_csv("data/master_panel_deduplicated.csv", index=False)
print(f"Saved deduplicated master panel to 'data/master_panel_deduplicated.csv'")

# After creating the master_clean panel, add this code to check for missingness

# 1. Check overall missingness by column
print("\n--- MISSINGNESS ANALYSIS ---")
missing_by_col = master_clean.isna().sum().sort_values(ascending=False)
missing_pct = (missing_by_col / len(master_clean) * 100).round(2)

# Create a summary DataFrame of missingness
missing_summary = pd.DataFrame({
    'Missing_Count': missing_by_col,
    'Missing_Percent': missing_pct
})

# Only show columns with some missing data
missing_cols = missing_summary[missing_summary['Missing_Count'] > 0]
print(f"\nColumns with missing values ({len(missing_cols)} of {len(missing_summary)} columns):")
print(missing_cols.head(15))  # Show top 15 columns with most missing values
print(f"... and {len(missing_cols) - 15} more columns with missing values" if len(missing_cols) > 15 else "")

# 2. Check completeness by source
print("\nMissingness by source:")
# Get columns from each source based on prefix
ref_cols = [col for col in master_clean.columns if col.startswith('ref_')]
bbg_cols = [col for col in master_clean.columns if col.startswith('bbg_')]
wrds_cols = [col for col in master_clean.columns if col.startswith('wrds_')]

# Calculate rows with missing data for each source
ref_missing = master_clean[ref_cols].isna().all(axis=1).sum()
bbg_missing = master_clean[bbg_cols].isna().all(axis=1).sum() if bbg_cols else len(master_clean)
wrds_missing = master_clean[wrds_cols].isna().all(axis=1).sum() if wrds_cols else len(master_clean)

print(f"Rows missing all Refinitiv data: {ref_missing} ({ref_missing/len(master_clean)*100:.1f}%)")
print(f"Rows missing all Bloomberg data: {bbg_missing} ({bbg_missing/len(master_clean)*100:.1f}%)")
print(f"Rows missing all WRDS data: {wrds_missing} ({wrds_missing/len(master_clean)*100:.1f}%)")

# 3. Check complete rows
complete_rows = master_clean.dropna().shape[0]
print(f"\nCompletely filled rows (no missing values): {complete_rows} ({complete_rows/len(master_clean)*100:.1f}%)")

# 4. Check for key variables used in regression analysis
key_vars = [
    # Try to find these variables with their new prefixes
    col for col in master_clean.columns if any(x in col.lower() for x in [
        'tobin', 'esg_score', 'pct_female', 'board_independence', 
        'esg_controversies', 'numberdirectors', 'roa', 'leverage', 'market_cap'
    ])
]

if key_vars:
    print("\nMissingness in potential regression variables:")
    key_vars_missing = master_clean[key_vars].isna().sum()
    key_vars_pct = (key_vars_missing / len(master_clean) * 100).round(2)
    key_missing = pd.DataFrame({
        'Missing_Count': key_vars_missing,
        'Missing_Percent': key_vars_pct
    })
    print(key_missing)

# 5. Save a detailed missingness report to data/ folder
missing_summary.to_csv("data/missingness_report.csv")
print("\nDetailed missingness report saved to 'data/missingness_report.csv'")

# Optional: Code for visualizing missing data with missingno package
print("\nTo visualize missing data patterns, consider using the following code:")

try:
    # Try with error handling to prevent crashes
    import missingno as msno
    import matplotlib.pyplot as plt
    
    # Create a smaller sample for better visualization performance
    sample_data = master_clean.sample(min(1000, len(master_clean)))
    
    # Matrix plot of missing values - use the original matrix() function
    plt.figure(figsize=(12, 8))
    msno.matrix(sample_data)  # Use original matrix function instead of nullity_matrix
    plt.title('Missing Value Matrix (Sample)')
    plt.savefig('data/missing_matrix.png')
    print("Created missing values matrix visualization")
    
    # Correlation heatmap - wrapped in try/except
    try:
        plt.figure(figsize=(10, 8))
        msno.heatmap(sample_data)
        plt.title('Correlation of Missingness')
        plt.savefig('data/missing_correlation.png')
        print("Created missingness correlation heatmap")
    except Exception as e:
        print(f"Could not create heatmap: {e}")
    
    # Bar chart visualization
    try:
        plt.figure(figsize=(10, 6))
        msno.bar(sample_data)
        plt.title('Missing Value Bar Chart')
        plt.savefig('data/missing_bar.png')
        print("Created missing values bar chart")
    except Exception as e:
        print(f"Could not create bar chart: {e}")
        
except ImportError:
    print("Could not import missingno. Install with 'pip install missingno'")
except Exception as e:
    print(f"Error creating visualizations: {e}")
    print("Consider updating missingno or matplotlib packages")

# Create a focused missingness analysis on regression variables
print("\n--- REGRESSION VARIABLES MISSINGNESS ANALYSIS ---")

# Define specific variables of interest by their likely column names
regression_vars = []

# Search for relevant variables using common naming patterns across all sources
var_patterns = {
    "Tobin's Q": ['tobin', 'tq'],
    "Leverage": ['leverage', 'debt_to_assets'],
    "Liquidity": ['liquidity', 'current_ratio'],
    "Board Size": ['board_size', 'numberdirectors', 'directors_total'],
    "Female Directors": ['female', 'women', 'gender', 'diversity'],
    "Board Independence": ['independence', 'independent_directors'],
    "ESG Score": ['esg_score', 'esg_combined'],
    "ESG Controversies": ['controversies', 'esg_contr'],
    "ROA": ['roa', 'return_on_assets'],
    "Market Cap": ['market_cap', 'marketcap']
}

# Find matching columns for each variable type
found_vars = {}
for var_type, patterns in var_patterns.items():
    matches = []
    for col in master_clean.columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in patterns):
            matches.append(col)
    
    if matches:
        found_vars[var_type] = matches
        regression_vars.extend(matches)

# Print which variables were found
print("\nFound regression variables:")
for var_type, cols in found_vars.items():
    print(f"{var_type}: {', '.join(cols)}")

# Get missingness statistics just for regression variables
if regression_vars:
    reg_missing = master_clean[regression_vars].isna().sum().sort_values(ascending=False)
    reg_missing_pct = (reg_missing / len(master_clean) * 100).round(2)
    
    # Create a summary DataFrame
    reg_missing_summary = pd.DataFrame({
        'Variable_Type': [next((k for k, v in found_vars.items() if col in v), "Other") for col in reg_missing.index],
        'Missing_Count': reg_missing,
        'Missing_Percent': reg_missing_pct
    })
    
    # Sort by variable type and missing percentage
    reg_missing_summary = reg_missing_summary.sort_values(['Variable_Type', 'Missing_Percent'], ascending=[True, False])
    
    print("\nMissingness in regression variables:")
    print(reg_missing_summary)
    
    # Check completeness for regression analysis
    complete_cases = master_clean.dropna(subset=regression_vars).shape[0]
    print(f"\nRows with complete data for ALL regression variables: {complete_cases} ({complete_cases/len(master_clean)*100:.1f}%)")
    
    # Source breakdown for regression variables
    print("\nSource of regression variables:")
    source_counts = {
        'Refinitiv': len([v for v in regression_vars if v.startswith('ref_')]),
        'Bloomberg': len([v for v in regression_vars if v.startswith('bbg_')]),
        'WRDS': len([v for v in regression_vars if v.startswith('wrds_')])
    }
    for source, count in source_counts.items():
        print(f"{source}: {count} variables")
    
    # Save regression variables missingness to CSV
    reg_missing_summary.to_csv("data/regression_vars_missingness.csv", index=True)
    print("\nDetailed regression variables missingness report saved to 'data/regression_vars_missingness.csv'")
    
    # Create visualizations specifically for regression variables
    try:
        import missingno as msno
        import matplotlib.pyplot as plt
        
        # Matrix plot for regression variables only
        plt.figure(figsize=(12, 8))
        msno.matrix(master_clean[regression_vars].sample(min(1000, len(master_clean))))
        plt.title('Missing Values in Regression Variables')
        plt.savefig('data/regression_vars_missing_matrix.png')
        print("Created missing values matrix for regression variables")
        
    except Exception as e:
        print(f"Could not create visualization for regression variables: {e}")
else:
    print("No matching regression variables found in the dataset.")