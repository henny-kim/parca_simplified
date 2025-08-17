# Adverse Event Extraction

This module provides comprehensive adverse event (AE) extraction from clinical studies using LLM (Gemini API) to analyze full text content.

## Overview

The adverse event extraction system:
- Fetches full text from PubMed Central (PMC) when available
- Uses LLM to extract structured adverse event data
- Generates a separate `adverse_event.json` file with detailed AE information
- Includes confidence scores and supporting quotes

## Features

### Extracted Data Types
- **Overall AE Rates**: Any grade, Grade 3-4, Serious AEs, Treatment-related AEs
- **Specific AEs**: Hematologic and non-hematologic adverse events with percentages
- **Management**: Discontinuation and dose reduction rates
- **Sample Size**: Total patients and patients with AEs
- **Context**: Supporting quotes and data source locations

### Data Structure
```json
{
  "pmid": "12345678",
  "citation": "Author et al. Study title...",
  "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
  "drug": "azacitidine",
  "any_grade_ae_rate": 85.5,
  "grade_3_4_ae_rate": 45.2,
  "serious_ae_rate": 25.0,
  "treatment_related_ae_rate": 75.0,
  "hematologic_ae": {
    "neutropenia": 45.2,
    "thrombocytopenia": 32.1,
    "anemia": 28.5
  },
  "non_hematologic_ae": {
    "nausea": 25.0,
    "fatigue": 30.5,
    "diarrhea": 15.2
  },
  "discontinuation_rate": 12.5,
  "dose_reduction_rate": 35.0,
  "total_patients": 100,
  "patients_with_ae": 85,
  "supporting_quotes": [
    "The most common grade 3-4 adverse events were neutropenia (45.2%) and thrombocytopenia (32.1%)"
  ],
  "data_source_location": "Results",
  "extraction_confidence": 0.85
}
```

## Usage

### Prerequisites
1. Set your Gemini API key:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Extraction

#### Full Extraction
Extract adverse events from all studies:
```bash
python extract_adverse_events.py
```

#### Test Extraction
Test with a small sample (first study from each drug):
```bash
python test_adverse_events.py
```

### Output Files
- `adverse_event.json`: Complete adverse event data for all studies
- `test_adverse_events.json`: Test results with sample studies

## Technical Details

### Full Text Access
The system prioritizes full text access in this order:
1. **PMC Full Text**: Fetches XML content from PubMed Central
2. **HTML Scraping**: Fallback to HTML content scraping
3. **Available Fields**: Uses existing extracted fields (key findings, etc.)

### LLM Processing
- Uses Gemini API for structured data extraction
- Comprehensive prompt engineering for medical data extraction
- Confidence scoring for extraction quality
- Rate limiting to avoid API limits

### Error Handling
- Graceful fallback when full text is unavailable
- Robust JSON parsing with validation
- Detailed error logging for debugging

## Integration

The adverse event data can be integrated with existing dashboards by:
1. Loading `adverse_event.json` alongside other data files
2. Displaying AE rates in safety sections
3. Providing drill-down capabilities to source studies

## Example Integration

```python
# Load adverse event data
with open('adverse_event.json', 'r') as f:
    ae_data = json.load(f)

# Access data for a specific drug
azacitidine_ae = ae_data['azacitidine']

# Get overall serious AE rate
serious_ae_rate = azacitidine_ae[0]['serious_ae_rate']
```

## Troubleshooting

### Common Issues
1. **API Key Not Set**: Ensure `GEMINI_API_KEY` environment variable is set
2. **Rate Limiting**: The script includes delays to avoid API limits
3. **Full Text Unavailable**: System falls back to available data fields
4. **JSON Parsing Errors**: Check LLM response format in logs

### Debugging
- Enable verbose logging by modifying print statements
- Check `test_adverse_events.json` for sample outputs
- Verify PMC access for specific PMIDs

## Future Enhancements

- Support for additional LLM providers (OpenAI, etc.)
- Enhanced full text extraction methods
- Real-time AE monitoring and updates
- Integration with clinical trial databases
- Automated AE trend analysis
