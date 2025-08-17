#!/usr/bin/env python3
"""
Simple Decitabine Clinical Efficacy Data Extraction for CMML Studies
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
    title = study.get('title', '')
    abstract = study.get('abstract', '')
    citation = study.get('citation', '')
    url = study.get('url', "https://pubmed.ncbi.nlm.nih.gov/" + str(pmid) + "/")
    
    # Check if study mentions CMML and decitabine
    text_to_check = (title + " " + abstract).lower()
    has_cmml = "cmml" in text_to_check or "chronic myelomonocytic leukemia" in text_to_check
    has_decitabine = "decitabine" in text_to_check
    
    # Basic summary
    if has_cmml and has_decitabine:
        efficacy_summary = "Study mentions CMML and decitabine treatment. LLM processing required for detailed efficacy data extraction."
        has_efficacy_data = True
    elif has_cmml:
        efficacy_summary = "Study mentions CMML but may not involve decitabine treatment. LLM processing required for detailed efficacy data extraction."
        has_efficacy_data = False
    else:
        efficacy_summary = "Study does not appear to focus on CMML treatment. LLM processing required for detailed efficacy data extraction."
        has_efficacy_data = False
    
    return ClinicalEfficacyData(
        pmid=pmid,
        citation=citation,
        url=url,
        drug='decitabine',
        supporting_quotes=[],
        data_source_location="title_or_abstract",
        extraction_confidence=0,
        efficacy_summary=efficacy_summary,
        has_efficacy_data=has_efficacy_data
    )

def main():
    # Load decitabine papers
    with open('pubmed_decitabine_cmml_complete.json', 'r') as f:
        pubmed_data = json.load(f)
    
    decitabine_papers = pubmed_data.get('decitabine', [])
    print("Processing " + str(len(decitabine_papers)) + " decitabine papers...")

    # Process all papers
    results = []
    
    for i, paper in enumerate(decitabine_papers, 1):
        print("Processing paper " + str(i) + "/" + str(len(decitabine_papers)) + ": PMID " + str(paper.get('pmid')))
        
        try:
            result = extract_basic_info(paper)
            results.append(asdict(result))
            
            if result.has_efficacy_data:
                print("    ✓ CMML + Decitabine mentioned")
            else:
                print("    ○ Basic info extracted")
                
        except Exception as e:
            print("    ✗ Error: " + str(e))
            continue

    # Save results
    output_file = 'Decitabine_extracted.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Summary
    with_efficacy = len([r for r in results if r.get('has_efficacy_data')])
    print("\n" + "="*60)
    print("DECITABINE BASIC EXTRACTION COMPLETED")
    print("="*60)
    print("Total papers processed: " + str(len(results)))
    if len(results) > 0:
        print("Papers with CMML + Decitabine: " + str(with_efficacy) + "/" + str(len(results)) + " (" + str(round(with_efficacy/len(results)*100, 1)) + "%)")
    else:
        print("Papers with CMML + Decitabine: 0/0 (0%)")
    print("Results saved to " + str(output_file))
    print("\nNOTE: This is a basic extraction. For detailed efficacy data, run the full LLM extraction script with GEMINI_API_KEY set.")

if __name__ == "__main__":
    main()
