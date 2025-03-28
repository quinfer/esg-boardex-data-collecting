import pandas as pd
import json

# First load master panel to get the correct time period
master_panel = pd.read_csv("data/master_panel_deduplicated.csv")

# Get the time range from the master panel
min_year = master_panel['fiscal_year'].min()
max_year = master_panel['fiscal_year'].max()

print(f"Creating template for period: {min_year} to {max_year}")

# Load the Refinitiv tickers from our previously saved JSON file
with open("data/refinitiv_unique_tickers.json", "r") as f:
    refinitiv_data = json.load(f)

# Create list of all company-year combinations
companies = []
dates = []
for ticker in refinitiv_data['tickers']:
    for year in range(min_year, max_year + 1):
        companies.append(f"{ticker} US Equity")
        dates.append(year)

# Create DataFrame with Bloomberg formatted tickers
bloomberg_template = pd.DataFrame({
    'Company': companies,
    'Dates': dates,
    'ESG_DISCLOSURE_SCORE': '',
    'SOCIAL_SCORE': '',
    'ESG_UNCERTAINTY_RANKING': ''
})

# Save template to CSV
bloomberg_template.to_csv("data/bloomberg_template.csv", index=False)

print(f"Created Bloomberg template with {len(refinitiv_data['tickers'])} companies")
print(f"Total rows: {len(bloomberg_template)} (companies × years)")
print("Template saved as 'data/bloomberg_template.csv'")

# Display first few rows as example
print("\nFirst few rows of the template:")
print(bloomberg_template.head())

# Print some summary statistics
print("\nTemplate Summary:")
print(f"Year range: {min_year}-{max_year}")
print(f"Number of years: {max_year - min_year + 1}")
print(f"Number of unique companies: {len(refinitiv_data['tickers'])}")