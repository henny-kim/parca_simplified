#!/usr/bin/env python3
"""
Test script for adverse event extraction
"""

import os
import json
from extract_adverse_events import AdverseEventExtractor, load_study_data, get_full_text_for_study

def test_adverse_event_extraction():
    """Test the adverse event extraction with a small sample"""
    
    # Get API key from environment
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    if not gemini_api_key:
        print("GEMINI_API_KEY not set. Please set the environment variable.")
        return
    
    # Initialize extractor
    try:
        extractor = AdverseEventExtractor(gemini_api_key)
        print("Successfully initialized adverse event extractor")
    except Exception as e:
        print(f"Failed to initialize extractor: {e}")
        return
    
    # Load study data
    input_file = 'cmml_detailed_outcomes.json'
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found")
        return
    
    study_data = load_study_data(input_file)
    
    # Test with first study from each drug
    test_results = {}
    
    for drug_name, studies in study_data.items():
        if studies:
            print(f"\nTesting {drug_name} with first study...")
            
            study = studies[0]
            print(f"  Study: PMID {study.get('pmid', 'N/A')}")
            
            # Get full text content
            full_text = get_full_text_for_study(study, extractor)
            print(f"  Full text length: {len(full_text)} characters")
            
            # Extract adverse events
            ae_data = extractor.extract_adverse_events(study, full_text)
            
            # Add drug information
            ae_data.drug = drug_name
            
            test_results[drug_name] = ae_data
            
            print(f"  Extraction completed")
            if ae_data.any_grade_ae_rate is not None:
                print(f"  Any grade AE rate: {ae_data.any_grade_ae_rate}%")
            if ae_data.grade_3_4_ae_rate is not None:
                print(f"  Grade 3-4 AE rate: {ae_data.grade_3_4_ae_rate}%")
            if ae_data.serious_ae_rate is not None:
                print(f"  Serious AE rate: {ae_data.serious_ae_rate}%")
    
    # Save test results
    output_file = 'test_adverse_events.json'
    with open(output_file, 'w') as f:
        # Convert dataclass objects to dictionaries
        test_dict = {}
        for drug_name, ae_data in test_results.items():
            test_dict[drug_name] = {
                'pmid': ae_data.pmid,
                'citation': ae_data.citation,
                'url': ae_data.url,
                'drug': ae_data.drug,
                'any_grade_ae_rate': ae_data.any_grade_ae_rate,
                'grade_3_4_ae_rate': ae_data.grade_3_4_ae_rate,
                'serious_ae_rate': ae_data.serious_ae_rate,
                'treatment_related_ae_rate': ae_data.treatment_related_ae_rate,
                'hematologic_ae': ae_data.hematologic_ae,
                'non_hematologic_ae': ae_data.non_hematologic_ae,
                'discontinuation_rate': ae_data.discontinuation_rate,
                'dose_reduction_rate': ae_data.dose_reduction_rate,
                'total_patients': ae_data.total_patients,
                'patients_with_ae': ae_data.patients_with_ae,
                'supporting_quotes': ae_data.supporting_quotes,
                'data_source_location': ae_data.data_source_location,
                'extraction_confidence': ae_data.extraction_confidence
            }
        json.dump(test_dict, f, indent=2)
    
    print(f"\nTest completed. Results saved to {output_file}")

if __name__ == "__main__":
    test_adverse_event_extraction()
