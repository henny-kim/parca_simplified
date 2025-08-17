# Decitabine Clinical Efficacy Extraction Summary

## Overview
Successfully extracted basic information from 125 decitabine papers related to CMML treatment and saved the results to `Decitabine_extracted.json`.

## Results Summary
- **Total papers processed**: 125
- **Papers with CMML + Decitabine mentioned**: 88 (70.4%)
- **Papers without CMML focus**: 37 (29.6%)
- **Output file**: `Decitabine_extracted.json` (108KB)

## File Structure
The extracted data follows the same structure as the azacitidine extraction:

```json
{
  "pmid": "string",
  "citation": "string", 
  "url": "string",
  "drug": "decitabine",
  "complete_response": null,
  "partial_response": null,
  "marrow_complete_response": null,
  "overall_response_rate": null,
  "progression_free_survival_median": null,
  "overall_survival_median": null,
  "total_patients": null,
  "cmml_patients": null,
  "supporting_quotes": [],
  "data_source_location": "title_or_abstract",
  "extraction_confidence": 0,
  "efficacy_summary": "string",
  "has_efficacy_data": boolean
}
```

## Current Status
- ✅ Basic extraction completed
- ✅ File structure matches azacitidine format
- ⏳ Detailed LLM extraction pending (requires GEMINI_API_KEY)

## Next Steps
To get detailed efficacy data (response rates, survival metrics, etc.), run the full LLM extraction script:

```bash
export GEMINI_API_KEY="your_api_key_here"
python extract_decitabine_efficacy.py
```

## Files Created
1. `Decitabine_extracted.json` - Main extraction results
2. `extract_decitabine_efficacy.py` - Full LLM extraction script
3. `extract_decitabine_simple.py` - Basic extraction script (used for initial setup)

## Key Papers Identified
The extraction identified 88 papers that specifically mention both CMML and decitabine treatment, including:

- Recent studies (2025) on oral decitabine/cedazuridine
- Combination therapy studies (decitabine + venetoclax)
- Phase 2 and 3 clinical trials
- Real-world evidence studies

These papers are ready for detailed LLM-based efficacy data extraction when the API key is available.
