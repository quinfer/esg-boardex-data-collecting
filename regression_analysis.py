import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Load the master panel created from the merge
master_panel = pd.read_csv("master_panel_refinitiv_based.csv")

# Print basic information about the dataset
print(f"Master panel contains {len(master_panel)} observations")
print(f"Time period covered: {master_panel['fiscal_year'].min()} to {master_panel['fiscal_year'].max()}")
print(f"Number of companies: {master_panel['ticker_clean'].nunique()}")

# Define variables for regression based on Table 2
# Check if the variables exist in the dataset
required_variables = [
    'tobins_q',                  # Dependent variable
    'esg_uncertainty_ranking',   # ESG variance across rating agencies
    'pct_female_directors',      # Board Gender Diversity Score
    'board_independence_pct',    # Board Independence
    'esg_score',                 # ESG Score
    'numberdirectors',           # Board Size
    'esg_controversies_score',   # ESG Controversies Score
    'roa',                       # ROA Total Assets
    'leverage_ratio',            # Leverage Ratio
    'market_cap'                 # Market Capital
]

# Check which variables are available in the dataset
available_vars = []
missing_vars = []
for var in required_variables:
    if var in master_panel.columns:
        available_vars.append(var)
    else:
        missing_vars.append(var)
        
print("\nVariables available for analysis:", available_vars)
print("Variables missing from dataset:", missing_vars)

# Create a subset of the data with only the variables needed for regression
# For missing variables, we'll look for similar columns that might have the data
regression_data = master_panel.copy()

# Handle potentially missing variables with alternative column names
col_mappings = {
    'tobins_q': ['tobins_q', 'tobin_q', 'tq'],
    'esg_uncertainty_ranking': ['esg_uncertainty_ranking', 'esg_uncertainty', 'esg_uncertainty_score'],
    'pct_female_directors': ['pct_female_directors', 'pct_women_board', 'board_gender_diversity_score'],
    'board_independence_pct': ['board_independence_pct', 'independent_directors_pct', 'board_independence'],
    'esg_score': ['esg_score', 'esg_combined_score', 'esg'],
    'numberdirectors': ['numberdirectors', 'board_size', 'directors_total'],
    'esg_controversies_score': ['esg_controversies_score', 'controversies_score', 'esg_controversies'],
    'roa': ['roa', 'return_on_assets', 'roa_total_assets'],
    'leverage_ratio': ['leverage_ratio', 'debt_to_assets', 'leverage'],
    'market_cap': ['market_cap', 'market_capital', 'marketcap']
}

# Try to find all required variables
found_vars = {}
for var, alternatives in col_mappings.items():
    for alt in alternatives:
        if alt in regression_data.columns:
            found_vars[var] = alt
            break

print("\nMatched variables:")
for std_name, actual_col in found_vars.items():
    print(f"{std_name} -> {actual_col}")

# Create log of market cap if available
if 'market_cap' in found_vars:
    regression_data['market_cap_log'] = np.log(regression_data[found_vars['market_cap']].replace(0, np.nan))
    found_vars['market_cap_log'] = 'market_cap_log'

# Filter rows with missing values in key variables
before_filter = len(regression_data)
regression_data = regression_data.dropna(subset=[found_vars.get(var, var) for var in required_variables if var in found_vars])
after_filter = len(regression_data)
print(f"\nFiltered out {before_filter - after_filter} rows with missing values ({(before_filter - after_filter)/before_filter*100:.1f}%)")

# Prepare regression formula
# Tobin's Q as dependent variable
dependent_var = found_vars.get('tobins_q', 'tobins_q')

# Independent variables
indep_vars = [found_vars.get(var, var) for var in required_variables[1:] if var in found_vars]
formula = f"{dependent_var} ~ {' + '.join(indep_vars)}"

print(f"\nRegression formula: {formula}")

# Check for multicollinearity
if len(indep_vars) > 0:
    # Create a dataframe for VIF calculation
    X = regression_data[indep_vars].copy()
    X = X.fillna(X.mean())  # Fill any remaining NA values for VIF calculation
    
    # Add constant
    X['const'] = 1
    
    # Calculate VIF
    vif_data = pd.DataFrame()
    vif_data["Variable"] = X.columns
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    
    print("\nMulticollinearity Check (VIF):")
    print(vif_data.sort_values('VIF', ascending=False))

# Run regression if we have enough variables
if len(indep_vars) >= 2:  # At least 2 independent variables
    try:
        model = smf.ols(formula=formula, data=regression_data).fit()
        
        # Print summary
        print("\nRegression Results:")
        print(model.summary())
        
        # Save regression results to file
        with open("regression_results.txt", "w") as f:
            f.write(model.summary().as_text())
            
        print("Full regression results saved to 'regression_results.txt'")
        
        # Diagnostic plots
        plt.figure(figsize=(12, 10))
        
        # Residuals vs Fitted
        plt.subplot(2, 2, 1)
        plt.scatter(model.fittedvalues, model.resid)
        plt.xlabel('Fitted values')
        plt.ylabel('Residuals')
        plt.title('Residuals vs Fitted')
        
        # QQ plot
        plt.subplot(2, 2, 2)
        from scipy import stats
        stats.probplot(model.resid, plot=plt)
        plt.title('Normal Q-Q')
        
        # Scale-Location
        plt.subplot(2, 2, 3)
        plt.scatter(model.fittedvalues, np.sqrt(np.abs(model.resid)))
        plt.xlabel('Fitted values')
        plt.ylabel('√|Residuals|')
        plt.title('Scale-Location')
        
        # Residuals vs Leverage
        plt.subplot(2, 2, 4)
        plt.scatter(model.get_influence().hat_matrix_diag, model.resid)
        plt.xlabel('Leverage')
        plt.ylabel('Residuals')
        plt.title('Residuals vs Leverage')
        
        plt.tight_layout()
        plt.savefig('regression_diagnostics.png')
        print("Diagnostic plots saved to 'regression_diagnostics.png'")
        
    except Exception as e:
        print(f"Error running regression: {e}")
else:
    print("\nNot enough variables available for meaningful regression.")

# Create year fixed effects model if we have enough years
if regression_data['fiscal_year'].nunique() > 2:
    try:
        # Add year dummies to the formula
        year_formula = formula + " + C(fiscal_year)"
        
        # Run regression with year fixed effects
        year_model = smf.ols(formula=year_formula, data=regression_data).fit()
        
        # Print summary
        print("\nRegression with Year Fixed Effects:")
        print(year_model.summary())
        
        # Save regression results to file
        with open("regression_results_with_year_fe.txt", "w") as f:
            f.write(year_model.summary().as_text())
            
        print("Year fixed effects regression results saved to 'regression_results_with_year_fe.txt'")
    except Exception as e:
        print(f"Error running year fixed effects regression: {e}")
