#!/usr/bin/env python3
"""
Working Clinical Efficacy Data Extraction for CMML Studies
"""

import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
import google.generativeai as genai

@dataclass
class ClinicalEfficacyData:
    pmid: str
    citation: str
    url: str
    drug: str
    
    # Efficacy metrics
    complete_response: Optional[float] = None
    partial_response: Optional[float] = None
    marrow_complete_response: Optional[float] = None
    overall_response_rate: Optional[float] = None
    
    # Survival metrics
    progression_free_survival_median: Optional[float] = None
    overall_survival_median: Optional[float] = None
    
    # Study details
    total_patients: Optional[int] = None
    cmml_patients: Optional[int] = None
    
    # Metadata
    supporting_quotes: List[str] = None
    data_source_location: str = ""
    extraction_confidence: Optional[float] = None
    efficacy_summary: str = ""
    has_efficacy_data: bool = False

    def __post_init__(self):
        if self.supporting_quotes is None:
            self.supporting_quotes = []

class ClinicalEfficacyExtractor:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def extract_clinical_efficacy(self, study: Dict[str, Any]) -> ClinicalEfficacyData:
        """Extract clinical efficacy data from a PubMed study."""
        
        pmid = study.get('pmid', '')
        title = study.get('title', '')
        abstract = study.get('abstract', '')
        citation = study.get('citation', '')
        url = study.get('url', "https://pubmed.ncbi.nlm.nih.gov/" + str(pmid) + "/")
        
        # Create combined text for analysis
        text_to_analyze = "Title: " + str(title) + "\n\nAbstract: " + str(abstract)
        
        prompt = """
You are a medical data extraction expert. Analyze this research paper and extract clinical efficacy data related to CMML (Chronic Myelomonocytic Leukemia) treatment.

PAPER TO ANALYZE:
""" + text_to_analyze + """

EXTRACTION TASK:
Extract the following clinical efficacy metrics if mentioned in the paper:

1. RESPONSE RATES (as percentages, e.g., 45.2% becomes 45.2):
   - Complete Response (CR) rate
   - Partial Response (PR) rate  
   - Marrow Complete Response (mCR) rate
   - Overall Response Rate (ORR) 

2. SURVIVAL METRICS (in months, e.g., 12.5 months becomes 12.5):
   - Progression-Free Survival (PFS) median
   - Overall Survival (OS) median

3. PATIENT NUMBERS (as integers):
   - Total number of patients in study
   - Number of CMML patients specifically

4. SUPPORTING INFORMATION:
   - Key quotes that support the extracted numbers
   - Confidence level (0-100) in the extraction accuracy
   - Brief summary of efficacy findings
   - Whether meaningful efficacy data was found (true/false)

IMPORTANT EXTRACTION RULES:
- Only extract numbers explicitly stated in the text
- Convert percentages to decimal numbers (e.g., 45% becomes 45.0)
- Convert survival times to months (e.g., 1.2 years becomes 14.4 months)
- If a range is given, use the median or primary value mentioned
- Include exact quotes that contain the numerical data
- Mark has_efficacy_data as true only if meaningful response rates or survival data is found

RESPONSE FORMAT (JSON):
{
    "complete_response": null_or_number,
    "partial_response": null_or_number,
    "marrow_complete_response": null_or_number,
    "overall_response_rate": null_or_number,
    "progression_free_survival_median": null_or_number,
    "overall_survival_median": null_or_number,
    "total_patients": null_or_number,
    "cmml_patients": null_or_number,
    "supporting_quotes": ["quote1", "quote2"],
    "extraction_confidence": confidence_score,
    "efficacy_summary": "brief_summary",
    "has_efficacy_data": true_or_false,
    "data_source_location": "title_or_abstract"
}

Provide only the JSON response, no additional text.
"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response text
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON response
            extracted_data = json.loads(response_text)
            
            # Create result object
            result = ClinicalEfficacyData(
                pmid=pmid,
                citation=citation,
                url=url,
                drug=study.get('drug', 'azacitidine'),
                complete_response=extracted_data.get('complete_response'),
                partial_response=extracted_data.get('partial_response'),
                marrow_complete_response=extracted_data.get('marrow_complete_response'),
                overall_response_rate=extracted_data.get('overall_response_rate'),
                progression_free_survival_median=extracted_data.get('progression_free_survival_median'),
                overall_survival_median=extracted_data.get('overall_survival_median'),
                total_patients=extracted_data.get('total_patients'),
                cmml_patients=extracted_data.get('cmml_patients'),
                supporting_quotes=extracted_data.get('supporting_quotes', []),
                data_source_location=extracted_data.get('data_source_location', ''),
                extraction_confidence=extracted_data.get('extraction_confidence'),
                efficacy_summary=extracted_data.get('efficacy_summary', ''),
                has_efficacy_data=extracted_data.get('has_efficacy_data', False)
            )
            
            return result
            
        except json.JSONDecodeError as e:
            print("JSON parsing error for PMID " + str(pmid) + ": " + str(e))
            print("Raw response: " + str(response_text[:200]) + "...")
            return self._create_error_result(study, "JSON parsing error: " + str(e))
            
        except Exception as e:
            error_msg = "Error extracting efficacy data for PMID " + str(pmid) + ": " + str(e)
            print(error_msg)
            return self._create_error_result(study, str(e))

    def _create_error_result(self, study: Dict[str, Any], error_msg: str) -> ClinicalEfficacyData:
        """Create an error result when extraction fails."""
        return ClinicalEfficacyData(
            pmid=study.get('pmid', ''),
            citation=study.get('citation', ''),
            url=study.get('url', "https://pubmed.ncbi.nlm.nih.gov/" + str(study.get('pmid', '')) + "/"),
            drug=study.get('drug', 'azacitidine'),
            data_source_location="Extraction failed",
            efficacy_summary=error_msg,
            has_efficacy_data=False
        )

def main():
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        return

    # Load azacitidine papers
    with open('pubmed_all_cmml_papers.json', 'r') as f:
        pubmed_data = json.load(f)
    
    azacitidine_papers = pubmed_data.get('azacitidine', [])
    print("Starting clinical efficacy extraction for " + str(len(azacitidine_papers)) + " azacitidine papers...")
    print("Rate limiting: 5 requests/minute (12s intervals), 50 requests/day max")
    print("Estimated time: " + str(round(min(50, len(azacitidine_papers)) * 12 / 60, 1)) + " minutes for first batch")
    print("Daily limit allows processing ~50 papers per day")

    # Check for existing checkpoint
    checkpoint_file = 'clinical_efficacy_azacitidine_checkpoint.json'
    results = []
    start_index = 0
    
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r') as f:
                results = json.load(f)
            start_index = len(results)
            print("Resuming from checkpoint: " + str(start_index) + " papers already processed")
        except:
            print("Checkpoint file corrupted, starting fresh")

    # Initialize extractor
    extractor = ClinicalEfficacyExtractor(api_key)
    
    # Process papers until API quota is reached
    requests_today = 0
    
    for i, paper in enumerate(azacitidine_papers[start_index:], start_index + 1):
        # No artificial limit - let it run until API quota is reached
            
        print("Processing paper " + str(i) + "/" + str(len(azacitidine_papers)) + ": PMID " + str(paper.get('pmid')) + " (Request #" + str(requests_today + 1) + " today)")
        
        try:
            result = extractor.extract_clinical_efficacy(paper)
            results.append(asdict(result))
            requests_today += 1
            
            if result.has_efficacy_data:
                print("    ✓ Efficacy data found")
            else:
                print("    ○ No efficacy data found")
                
        except Exception as e:
            error_str = str(e)
            print("    ✗ Error: " + error_str)
            
            # Check if this is an API quota error
            if "quota" in error_str.lower() or "limit" in error_str.lower() or "429" in error_str:
                print("\n" + "="*60)
                print("*** API QUOTA LIMIT REACHED ***")
                print("Stopped at paper " + str(i) + "/" + str(len(azacitidine_papers)))
                print("Total requests made: " + str(requests_today))
                print("Papers processed successfully: " + str(len(results)))
                print("="*60)
                break
            else:
                # Continue with next paper for other errors
                continue
        
        # Save checkpoint every 10 papers
        if i % 10 == 0:
            with open(checkpoint_file, 'w') as f:
                json.dump(results, f, indent=2)
            print("*** CHECKPOINT: " + str(i) + "/" + str(len(azacitidine_papers)) + " papers processed ***")
            
        # Respect rate limits: 5 requests per minute = 12 second intervals
        if i < len(azacitidine_papers):  # Don't wait after last paper
            print("    Waiting 12 seconds for rate limiting...")
            time.sleep(12)

    # Save results
    output_file = 'clinical_efficacy_azacitidine.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Summary
    with_efficacy = len([r for r in results if r.get('has_efficacy_data')])
    print("\n" + "="*60)
    print("CLINICAL EFFICACY EXTRACTION COMPLETED")
    print("="*60)
    print("Total papers processed: " + str(len(results)))
    if len(results) > 0:
        print("Papers with efficacy data: " + str(with_efficacy) + "/" + str(len(results)) + " (" + str(round(with_efficacy/len(results)*100, 1)) + "%)")
    else:
        print("Papers with efficacy data: 0/0 (0%)")
    print("Results saved to " + str(output_file))

if __name__ == "__main__":
    main()
