#!/usr/bin/env python3
"""
Enhanced Clinical Efficacy Data Extraction
Improved prompts to capture PFS, therapy duration, and comprehensive adverse events
"""

import json
import os
import time
import google.generativeai as genai
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

@dataclass
class EnhancedClinicalEfficacyData:
    pmid: str
    citation: str
    url: str
    drug: str
    
    # Efficacy metrics
    complete_response: Optional[float] = None
    partial_response: Optional[float] = None
    marrow_complete_response: Optional[float] = None
    overall_response_rate: Optional[float] = None
    
    # Survival metrics (enhanced)
    progression_free_survival_median: Optional[float] = None
    progression_free_survival_mean: Optional[float] = None
    progression_free_survival_range: Optional[str] = None
    overall_survival_median: Optional[float] = None
    overall_survival_mean: Optional[float] = None
    overall_survival_range: Optional[str] = None
    
    # Therapy duration (new)
    therapy_duration_median: Optional[float] = None
    therapy_duration_mean: Optional[float] = None
    therapy_duration_range: Optional[str] = None
    therapy_cycles_median: Optional[float] = None
    therapy_cycles_mean: Optional[float] = None
    therapy_cycles_range: Optional[str] = None
    
    # Patient data
    total_patients: Optional[int] = None
    cmml_patients: Optional[int] = None
    
    # Adverse events (enhanced)
    any_grade_ae_rate: Optional[float] = None
    grade_3_4_ae_rate: Optional[float] = None
    serious_ae_rate: Optional[float] = None
    treatment_related_ae_rate: Optional[float] = None
    discontinuation_rate: Optional[float] = None
    dose_reduction_rate: Optional[float] = None
    
    # Supporting data
    supporting_quotes: List[str] = None
    data_source_location: str = "abstract"
    extraction_confidence: int = 0
    efficacy_summary: str = ""
    has_efficacy_data: bool = False
    
    def __post_init__(self):
        if self.supporting_quotes is None:
            self.supporting_quotes = []

def extract_enhanced_clinical_efficacy(study: Dict[str, Any]) -> EnhancedClinicalEfficacyData:
    """Extract enhanced clinical efficacy data with improved prompts"""
    
    pmid = study.get('pmid', '')
    title = study.get('title', '')
    abstract = study.get('abstract', '')
    url = study.get('url', "https://pubmed.ncbi.nlm.nih.gov/" + str(pmid) + "/")
    
    text_to_analyze = "Title: " + str(title) + "\n\nAbstract: " + str(abstract)
    
    # Enhanced prompt with specific focus on CMML-only data
    prompt = """You are a medical data extraction specialist. Analyze the following clinical study text and extract comprehensive clinical efficacy data for CMML (Chronic Myelomonocytic Leukemia) treatment ONLY.

CRITICAL: This study must contain CMML-specific data. If the study only contains data for MDS (Myelodysplastic Syndrome) or MPS/MPD (Myeloproliferative Syndrome/Disorder) without CMML patients, mark has_efficacy_data as false.

STUDY TEXT:
""" + text_to_analyze + """

EXTRACTION REQUIREMENTS:
1. **CMML-SPECIFIC DATA VERIFICATION**:
   - Study must include CMML patients specifically
   - Look for: "CMML", "chronic myelomonocytic leukemia", "CMML patients"
   - If study only mentions MDS or MPS/MPD without CMML, mark as no efficacy data
   - If study includes mixed populations, extract only CMML-specific data when available

2. **EFFICACY METRICS** - Extract CMML-specific response rates:
   - Complete Response (CR) rate for CMML patients (%)
   - Partial Response (PR) rate for CMML patients (%)
   - Marrow Complete Response rate for CMML patients (%)
   - Overall Response Rate (ORR) for CMML patients (%)

3. **SURVIVAL METRICS** - Extract CMML-specific survival data:
   - Progression-Free Survival (PFS) for CMML patients - median, mean, range (months)
   - Overall Survival (OS) for CMML patients - median, mean, range (months)
   - Look for: "median PFS", "PFS", "progression-free", "time to progression" in CMML cohort
   - Look for: "median OS", "overall survival", "OS" in CMML cohort

4. **THERAPY DURATION** - Extract CMML-specific treatment duration:
   - Duration of therapy for CMML patients (months/weeks)
   - Number of cycles administered to CMML patients
   - Look for: "cycles", "duration", "treatment period", "median cycles" in CMML cohort

5. **ADVERSE EVENTS** - Extract CMML-specific safety data:
   - Any grade AE rate in CMML patients (%)
   - Grade 3-4 AE rate in CMML patients (%)
   - Serious AE rate in CMML patients (%)
   - Treatment-related AE rate in CMML patients (%)
   - Discontinuation rate in CMML patients (%)
   - Dose reduction rate in CMML patients (%)

6. **PATIENT DATA**:
   - Total patients in study
   - Number of CMML patients specifically (this is critical)

IMPORTANT RULES:
- ONLY extract data if CMML patients are specifically mentioned
- If study only has MDS or MPS/MPD data without CMML, mark has_efficacy_data as false
- If study has mixed population, extract CMML-specific data when available
- If CMML data is not separately reported, mark as no efficacy data
- Be thorough but ONLY for CMML-specific outcomes

OUTPUT FORMAT (JSON):
{
  "complete_response": <number or null - CMML patients only>,
  "partial_response": <number or null - CMML patients only>,
  "marrow_complete_response": <number or null - CMML patients only>,
  "overall_response_rate": <number or null - CMML patients only>,
  "progression_free_survival_median": <number or null - CMML patients only>,
  "progression_free_survival_mean": <number or null - CMML patients only>,
  "progression_free_survival_range": <string or null - CMML patients only>,
  "overall_survival_median": <number or null - CMML patients only>,
  "overall_survival_mean": <number or null - CMML patients only>,
  "overall_survival_range": <string or null - CMML patients only>,
  "therapy_duration_median": <number or null - CMML patients only>,
  "therapy_duration_mean": <number or null - CMML patients only>,
  "therapy_duration_range": <string or null - CMML patients only>,
  "therapy_cycles_median": <number or null - CMML patients only>,
  "therapy_cycles_mean": <number or null - CMML patients only>,
  "therapy_cycles_range": <string or null - CMML patients only>,
  "total_patients": <number or null - total study patients>,
  "cmml_patients": <number or null - CMML patients specifically>,
  "any_grade_ae_rate": <number or null - CMML patients only>,
  "grade_3_4_ae_rate": <number or null - CMML patients only>,
  "serious_ae_rate": <number or null - CMML patients only>,
  "treatment_related_ae_rate": <number or null - CMML patients only>,
  "discontinuation_rate": <number or null - CMML patients only>,
  "dose_reduction_rate": <number or null - CMML patients only>,
  "supporting_quotes": ["quote1", "quote2"],
  "efficacy_summary": "brief summary focusing on CMML-specific outcomes",
  "has_efficacy_data": <boolean - true only if CMML-specific data found>,
  "extraction_confidence": <0-100>
}"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract JSON from response - more robust parsing
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        elif response_text.startswith('```'):
            response_text = response_text[3:]
        
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        # Clean up any extra text before or after JSON
        response_text = response_text.strip()
        
        # Try to find JSON object boundaries
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != 0:
            response_text = response_text[start_idx:end_idx]
        
        extracted_data = json.loads(response_text.strip())
        
        # Create EnhancedClinicalEfficacyData object
        efficacy_data = EnhancedClinicalEfficacyData(
            pmid=pmid,
            citation=study.get('citation', ''),
            url=url,
            drug=study.get('drug', 'azacitidine'),
            complete_response=extracted_data.get('complete_response'),
            partial_response=extracted_data.get('partial_response'),
            marrow_complete_response=extracted_data.get('marrow_complete_response'),
            overall_response_rate=extracted_data.get('overall_response_rate'),
            progression_free_survival_median=extracted_data.get('progression_free_survival_median'),
            progression_free_survival_mean=extracted_data.get('progression_free_survival_mean'),
            progression_free_survival_range=extracted_data.get('progression_free_survival_range'),
            overall_survival_median=extracted_data.get('overall_survival_median'),
            overall_survival_mean=extracted_data.get('overall_survival_mean'),
            overall_survival_range=extracted_data.get('overall_survival_range'),
            therapy_duration_median=extracted_data.get('therapy_duration_median'),
            therapy_duration_mean=extracted_data.get('therapy_duration_mean'),
            therapy_duration_range=extracted_data.get('therapy_duration_range'),
            therapy_cycles_median=extracted_data.get('therapy_cycles_median'),
            therapy_cycles_mean=extracted_data.get('therapy_cycles_mean'),
            therapy_cycles_range=extracted_data.get('therapy_cycles_range'),
            total_patients=extracted_data.get('total_patients'),
            cmml_patients=extracted_data.get('cmml_patients'),
            any_grade_ae_rate=extracted_data.get('any_grade_ae_rate'),
            grade_3_4_ae_rate=extracted_data.get('grade_3_4_ae_rate'),
            serious_ae_rate=extracted_data.get('serious_ae_rate'),
            treatment_related_ae_rate=extracted_data.get('treatment_related_ae_rate'),
            discontinuation_rate=extracted_data.get('discontinuation_rate'),
            dose_reduction_rate=extracted_data.get('dose_reduction_rate'),
            supporting_quotes=extracted_data.get('supporting_quotes', []),
            efficacy_summary=extracted_data.get('efficacy_summary', ''),
            has_efficacy_data=extracted_data.get('has_efficacy_data', False),
            extraction_confidence=extracted_data.get('extraction_confidence', 0)
        )
        
        return efficacy_data
        
    except Exception as e:
        print("    ✗ Error: " + str(e))
        # Return empty data structure
        return EnhancedClinicalEfficacyData(
            pmid=pmid,
            citation=study.get('citation', ''),
            url=url,
            drug=study.get('drug', 'azacitidine'),
            has_efficacy_data=False,
            extraction_confidence=0
        )

def main():
    """Main extraction function"""
    print("🔍 Loading azacitidine papers...")
    
    # Load papers
    with open('pubmed_all_cmml_papers.json', 'r') as f:
        all_papers = json.load(f)
    
    azacitidine_papers = all_papers.get('azacitidine', [])
    print(f"✅ Loaded {len(azacitidine_papers)} azacitidine papers")
    
    # Load checkpoint if exists
    checkpoint_file = 'clinical_efficacy_azacitidine_enhanced_checkpoint.json'
    results = []
    start_index = 0
    
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            results = json.load(f)
        start_index = len(results)
        print(f"📂 Resuming from checkpoint: {start_index} papers already processed")
    
    # Process papers
    requests_today = 0
    with_efficacy = 0
    
    for i, paper in enumerate(azacitidine_papers[start_index:], start_index + 1):
        print(f"📄 Processing paper {i}/{len(azacitidine_papers)}: PMID {paper.get('pmid', 'N/A')}")
        
        try:
            efficacy_data = extract_enhanced_clinical_efficacy(paper)
            results.append(asdict(efficacy_data))
            requests_today += 1
            
            if efficacy_data.has_efficacy_data:
                with_efficacy += 1
                print(f"    ✅ Extracted efficacy data (confidence: {efficacy_data.extraction_confidence}%)")
            else:
                print(f"    ⚠️  No efficacy data found")
            
            # Save checkpoint every 10 papers
            if i % 10 == 0:
                with open(checkpoint_file, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"💾 Checkpoint saved: {len(results)} papers processed")
            
            # Rate limiting
            time.sleep(1)
            
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
    
    # Save final results
    output_file = 'clinical_efficacy_azacitidine_enhanced.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 ENHANCED CLINICAL EFFICACY EXTRACTION SUMMARY")
    print("="*60)
    print("Total papers processed: " + str(len(results)))
    print("Papers with efficacy data: " + str(with_efficacy) + "/" + str(len(results)) + " (" + str(round(with_efficacy/len(results)*100, 1)) + "%)")
    print("API requests used: " + str(requests_today))
    print("Output saved to: " + output_file)
    print("Checkpoint saved to: " + checkpoint_file)
    
    # Calculate statistics for key metrics
    if len(results) > 0:
        pfs_data = [r['progression_free_survival_median'] for r in results if r['progression_free_survival_median'] is not None]
        os_data = [r['overall_survival_median'] for r in results if r['overall_survival_median'] is not None]
        therapy_cycles = [r['therapy_cycles_median'] for r in results if r['therapy_cycles_median'] is not None]
        ae_data = [r['serious_ae_rate'] for r in results if r['serious_ae_rate'] is not None]
        
        print(f"\n📈 DATA AVAILABILITY:")
        print(f"PFS data: {len(pfs_data)} papers")
        print(f"OS data: {len(os_data)} papers") 
        print(f"Therapy cycles: {len(therapy_cycles)} papers")
        print(f"Serious AE data: {len(ae_data)} papers")

if __name__ == "__main__":
    main()
