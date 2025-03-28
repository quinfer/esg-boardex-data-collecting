# Bloomberg Data Collection Instructions

## Overview
This document provides step-by-step instructions for downloading ESG and social score data from Bloomberg using our prepared template.

## Required Data Fields
- ESG_DISCLOSURE_SCORE
- SOCIAL_SCORE 
- ESG_UNCERTAINTY_RANKING

## Steps

### 1. Accessing Bloomberg Terminal
- Log into a Bloomberg Terminal
- Ensure you have access to Excel add-in functionality

### 2. Template Preparation
- Locate the `bloomberg_template.csv` file in your data folder
- Open the file in Excel
- Verify company identifiers are correctly formatted (e.g., "AAPL US Equity")

### 3. Data Import Process
1. On Bloomberg Terminal:
   - Type `XLTP <GO>`
   - This opens the Excel template tool

2. In the Excel Add-in:
   - Click "Import Template"
   - Select your prepared CSV file
   - Verify the company identifiers are recognized

3. Field Mapping:
   - Map the Bloomberg fields:
     * ESG_DISCLOSURE_SCORE
     * SOCIAL_SCORE
     * ESG_UNCERTAINTY_RANKING
   - Set periodicity to "Annual"
   - Set to "Fiscal Year" basis
   - Set date range to match your template years

4. Data Download:
   - Execute the download
   - Wait for completion (may take several minutes)
   - Save as "Bloomberg_unbalanced_2025.xlsx"

### 4. Quality Checks
Before closing:
- Verify data downloaded for all years
- Check for any error messages
- Ensure no missing identifiers
- Save a backup copy

### 5. File Management
- Save the final file as "Bloomberg_unbalanced_2025.xlsx"
- Place in your data/ directory
- Keep the original template as backup

## Notes
- Bloomberg data access required
- Large downloads may need to be done in batches
- Some companies may have missing data
- Consider downloading additional fields if available

## Troubleshooting
- If download fails, try smaller batches
- Verify Bloomberg codes are current
- Check terminal access permissions
- For persistent issues, consult Bloomberg help desk
