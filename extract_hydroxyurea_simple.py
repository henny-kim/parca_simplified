#!/usr/bin/env python3
"""
Simple Hydroxyurea Clinical Efficacy Data Extraction for CMML Studies
Creates basic structure without LLM processing
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

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

def extract_basic_info(study: Dict[str, Any]) -> ClinicalEfficacyData:
    """Extract basic information from study without LLM processing."""
    
    pmid = study.get('pmid', '')
    citation = study.get('citation', '')
    key_findings = study.get('key_findings', '')
    patient_population = study.get('patient_population', '')
    treatment_details = study.get('treatment_details', '')
    supporting_quotes = study.get('supporting_quotes', [])
    url = study.get('url', "https://pubmed.ncbi.nlm.nih.gov/" + str(pmid) + "/")
    
    # Check if study mentions CMML and hydroxyurea
    text_to_check = (citation + " " + key_findings + " " + patient_population + " " + treatment_details).lower()
    has_cmml = "cmml" in text_to_check or "chronic myelomonocytic leukemia" in text_to_check
    has_hydroxyurea = "hydroxyurea" in text_to_check or "hu" in text_to_check
    
    # Basic summary
    if has_cmml and has_hydroxyurea:
        efficacy_summary = "Study mentions CMML and hydroxyurea treatment. LLM processing required for detailed efficacy data extraction."
        has_efficacy_data = True
    elif has_cmml:
        efficacy_summary = "Study mentions CMML but may not involve hydroxyurea treatment. LLM processing required for detailed efficacy data extraction."
        has_efficacy_data = False
    else:
        efficacy_summary = "Study does not appear to focus on CMML treatment. LLM processing required for detailed efficacy data extraction."
        has_efficacy_data = False
    
    return ClinicalEfficacyData(
        pmid=pmid,
        citation=citation,
        url=url,
        drug='hydroxyurea',
        supporting_quotes=[],
        data_source_location="title_or_abstract",
        extraction_confidence=0,
        efficacy_summary=efficacy_summary,
        has_efficacy_data=has_efficacy_data
    )

def main():
    # Load hydroxyurea papers from the existing data
    with open('data/cmml_detailed_outcomes.json', 'r') as f:
        data = json.load(f)
    
    hydroxyurea_papers = data.get('hydroxyurea', [])
    print("Processing " + str(len(hydroxyurea_papers)) + " hydroxyurea papers...")

    # Process all papers
    results = []
    
    for i, paper in enumerate(hydroxyurea_papers, 1):
        print("Processing paper " + str(i) + "/" + str(len(hydroxyurea_papers)) + ": PMID " + str(paper.get('pmid')))
        
        try:
            result = extract_basic_info(paper)
            results.append(asdict(result))
            
            if result.has_efficacy_data:
                print("    ✓ CMML + Hydroxyurea mentioned")
            else:
                print("    ○ Basic info extracted")
                
        except Exception as e:
            print("    ✗ Error: " + str(e))
            continue

    # Save results
    output_file = 'Hydroxyurea_extracted.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Summary
    with_efficacy = len([r for r in results if r.get('has_efficacy_data')])
    print("\n" + "="*60)
    print("HYDROXYUREA BASIC EXTRACTION COMPLETED")
    print("="*60)
    print("Total papers processed: " + str(len(results)))
    if len(results) > 0:
        print("Papers with CMML + Hydroxyurea: " + str(with_efficacy) + "/" + str(len(results)) + " (" + str(round(with_efficacy/len(results)*100, 1)) + "%)")
    else:
        print("Papers with CMML + Hydroxyurea: 0/0 (0%)")
    print("Results saved to " + str(output_file))
    print("\nNOTE: This is a basic extraction. For detailed efficacy data, run the full LLM extraction script with GEMINI_API_KEY set.")

if __name__ == "__main__":
    main()
