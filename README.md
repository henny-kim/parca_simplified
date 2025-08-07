# Clinical Outcomes Data Extractor for CMML Drugs

This repository contains Python scripts that use AI-like pattern matching and PubMed API to extract structured clinical outcomes data for drugs used in Chronic Myelomonocytic Leukemia (CMML).

## Scripts

### 1. `clinical_data_extractor.py`
Basic script that extracts data for azacitidine in CMML.

### 2. `advanced_clinical_extractor.py`
Advanced script that extracts and compares data for all three drugs:
- Azacitidine
- Decitabine  
- Hydroxyurea

## Features

- **PubMed API Integration**: Automatically searches PubMed for relevant studies
- **AI-like Pattern Matching**: Uses regex patterns to extract clinical data from abstracts
- **Structured Data Extraction**: Extracts response rates, survival outcomes, and adverse events
- **Comparative Analysis**: Generates comparative reports between drugs
- **Citation Tracking**: Links all data points to their source studies

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. (Optional) Get a PubMed API key for higher rate limits:
   - Visit: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/
   - Add your API key to the script

## Usage

### Basic Script (Azacitidine only)
```bash
python clinical_data_extractor.py
```

### Advanced Script (All three drugs)
```bash
python advanced_clinical_extractor.py
```

## Output Files

The scripts generate:
1. **Markdown Report**: Structured clinical outcomes report
2. **JSON Data**: Raw extracted data for further analysis
3. **Console Summary**: Quick overview of extracted data points

## Extracted Data Types

### Response Rates
- Overall Response Rate (ORR)
- Complete Response (CR)
- Partial Response (PR)
- Marrow CR (mCR)
- Hematologic Improvement (HI)

### Survival Outcomes
- Median Overall Survival (OS)
- Median Progression-Free Survival (PFS)
- Median Event-Free Survival (EFS)

### Adverse Events
- Grade 3-4 Neutropenia
- Grade 3-4 Thrombocytopenia
- Febrile Neutropenia
- Anemia
- Infections

## Example Output

The advanced script generates a comparative table like:

| Drug | ORR (%) | CR (%) | Median OS (months) | Median PFS (months) | Studies |
|------|---------|--------|-------------------|-------------------|---------|
| Azacitidine | 45.2 | 15.8 | 16.3 | 8.7 | 12 |
| Decitabine | 52.1 | 18.4 | 18.9 | 10.2 | 8 |
| Hydroxyurea | 35.7 | 8.9 | 12.1 | 6.3 | 5 |

## Limitations

1. **Pattern Matching**: Relies on consistent text patterns in abstracts
2. **Data Quality**: Depends on how data is reported in publications
3. **Rate Limits**: PubMed API has rate limits (3 requests/second without API key)
4. **Abstract Only**: Only analyzes abstracts, not full papers

## Customization

You can modify the scripts to:
- Add new drugs by updating the `drugs` dictionary
- Add new data extraction patterns
- Change search queries
- Modify output formats

## Citation

When using this data, please cite the original studies identified by the PMIDs in the reports. # parca__cmml
# parca_cmml
# parca_gemini_cmml
