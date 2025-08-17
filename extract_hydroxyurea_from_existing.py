#!/usr/bin/env python3
"""
Extract Hydroxyurea Clinical Efficacy Data from Existing Data
Uses the existing cmml_detailed_outcomes.json file which has rich data
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

def extract_from_existing_data(study: Dict[str, Any]) -> ClinicalEfficacyData:
    """Extract clinical efficacy data from existing study data."""
    
    pmid = study.get('pmid', '')
    citation = study.get('citation', '')
    url = study.get('url', "https://pubmed.ncbi.nlm.nih.gov/" + str(pmid) + "/")
    key_findings = study.get('key_findings', '')
    patient_population = study.get('patient_population', '')
    treatment_details = study.get('treatment_details', '')
    supporting_quotes = study.get('supporting_quotes', [])
    cmml_sample_size = study.get('cmml_sample_size')
    
    # Check if study mentions CMML and hydroxyurea
    text_to_check = (citation + " " + key_findings + " " + patient_population + " " + treatment_details).lower()
    has_cmml = "cmml" in text_to_check or "chronic myelomonocytic leukemia" in text_to_check
    has_hydroxyurea = "hydroxyurea" in text_to_check or "hu" in text_to_check
    
    # Check for efficacy data in the existing fields
    has_efficacy_data = False
    efficacy_summary = ""
    
    if has_cmml and has_hydroxyurea:
        # Look for specific efficacy mentions
        if any(keyword in text_to_check for keyword in ['response', 'survival', 'efficacy', 'outcome', 'improvement']):
            has_efficacy_data = True
            efficacy_summary = f"Study contains CMML and hydroxyurea treatment data. Key findings: {key_findings}"
        else:
            efficacy_summary = "Study mentions CMML and hydroxyurea but no specific efficacy metrics found."
    elif has_cmml:
        efficacy_summary = "Study mentions CMML but may not involve hydroxyurea treatment."
    else:
        efficacy_summary = "Study does not appear to focus on CMML treatment."
    
    # Extract patient numbers
    total_patients = None
    cmml_patients = cmml_sample_size
    
    # Try to extract numbers from text
    import re
    
    # Look for patient numbers in text
    patient_patterns = [
        r'(\d+)\s*patients',
        r'(\d+)\s*CMML\s*patients',
        r'n\s*=\s*(\d+)',
        r'(\d+)\s*subjects'
    ]
    
    for pattern in patient_patterns:
        matches = re.findall(pattern, text_to_check)
        if matches:
            if not total_patients:
                total_patients = int(matches[0])
            if not cmml_patients and 'cmml' in pattern:
                cmml_patients = int(matches[0])
    
    return ClinicalEfficacyData(
        pmid=pmid,
        citation=citation,
        url=url,
        drug='hydroxyurea',
        total_patients=total_patients,
        cmml_patients=cmml_patients,
        supporting_quotes=supporting_quotes,
        data_source_location=study.get('data_source_location', ''),
        extraction_confidence=100 if has_efficacy_data else 0,
        efficacy_summary=efficacy_summary,
        has_efficacy_data=has_efficacy_data
    )

def main():
    """Main function to extract hydroxyurea data from existing data."""
    
    # Load existing hydroxyurea data
    with open('data/cmml_detailed_outcomes.json', 'r') as f:
        data = json.load(f)
    
    hydroxyurea_papers = data.get('hydroxyurea', [])
    print("Processing " + str(len(hydroxyurea_papers)) + " hydroxyurea papers from existing data...")

    # Process all papers
    results = []
    
    for i, paper in enumerate(hydroxyurea_papers, 1):
        print("Processing paper " + str(i) + "/" + str(len(hydroxyurea_papers)) + ": PMID " + str(paper.get('pmid')))
        
        try:
            result = extract_from_existing_data(paper)
            results.append(asdict(result))
            
            if result.has_efficacy_data:
                print("    ✓ CMML + Hydroxyurea with efficacy data")
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
    print("HYDROXYUREA EXTRACTION FROM EXISTING DATA COMPLETED")
    print("="*60)
    print("Total papers processed: " + str(len(results)))
    if len(results) > 0:
        print("Papers with CMML + Hydroxyurea + efficacy data: " + str(with_efficacy) + "/" + str(len(results)) + " (" + str(round(with_efficacy/len(results)*100, 1)) + "%)")
    else:
        print("Papers with CMML + Hydroxyurea + efficacy data: 0/0 (0%)")
    print("Results saved to " + str(output_file))
    
    # Show sample papers with efficacy data
    if with_efficacy > 0:
        print(f"\nSample papers with efficacy data:")
        for i, result in enumerate([r for r in results if r.get('has_efficacy_data')][:3]):
            print(f"{i+1}. PMID: {result['pmid']}")
            print(f"   Citation: {result['citation'][:100]}...")
            print(f"   Summary: {result['efficacy_summary'][:100]}...")
            print()

if __name__ == "__main__":
    main()
