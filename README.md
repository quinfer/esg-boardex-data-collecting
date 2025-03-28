# S&P 500 ESG and Board Diversity Analysis

This repository contains code and documentation for analyzing ESG performance, board gender diversity, and firm financial performance in S&P 500 companies.

## Project Structure

```
.
├── data/                      # Data directory (not tracked in git)
├── docs/                      # Documentation
│   ├── SP500_Governance_Panel_README.qmd
│   └── bloomberg_data_collection.md
├── scripts/                   # Python scripts
│   ├── merge_with_refinitiv_bloomberg.py
│   └── create_bloomberg_template.py
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Data Sources

- **Refinitiv**: ESG scores and board independence metrics
- **Bloomberg**: Alternative ESG scores and ratings
- **WRDS/BoardEx**: Board composition data and financial metrics

## Setup

1. Clone the repository
2. Create a `data` directory
3. Place your data files in the `data` directory:
   - Bloomberg_unbalanced_2025.xlsx
   - Refinitiv_Unbalanced_2025.xlsx
   - sp500_panel_with_diversity.csv

## Usage

1. Run the merge script to create the master panel:
   ```bash
   python scripts/merge_with_refinitiv_bloomberg.py
   ```

2. Generate Bloomberg template:
   ```bash
   python scripts/create_bloomberg_template.py
   ```

3. Follow instructions in `docs/bloomberg_data_collection.md` to update Bloomberg data

## Documentation

- `SP500_Governance_Panel_README.qmd`: Detailed documentation of the master panel
- `bloomberg_data_collection.md`: Instructions for Bloomberg data collection

## License

[Add your license information here]
