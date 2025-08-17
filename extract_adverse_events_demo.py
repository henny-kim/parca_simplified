#!/usr/bin/env python3
"""
Demonstration version of adverse event extraction that works without LLM API
Uses pattern matching and text analysis to extract adverse event data
"""

import json
import re
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class AdverseEventData:
    """Data structure for adverse event information"""
    pmid: str
    citation: str
    url: str
    drug: str = ""
    
    # Overall adverse event rates
    any_grade_ae_rate: Optional[float] = None
    grade_3_4_ae_rate: Optional[float] = None
    serious_ae_rate: Optional[float] = None
    treatment_related_ae_rate: Optional[float] = None
    
    # Specific adverse events
    hematologic_ae: Optional[Dict[str, float]] = None
    non_hematologic_ae: Optional[Dict[str, float]] = None
    
    # Discontinuation due to AEs
    discontinuation_rate: Optional[float] = None
    dose_reduction_rate: Optional[float] = None
    
    # Sample size
    total_patients: Optional[int] = None
    patients_with_ae: Optional[int] = None
    
    # Supporting quotes and context
    supporting_quotes: List[str] = None
    data_source_location: str = "Unknown"
    extraction_confidence: Optional[float] = None
    
    def __post_init__(self):
        if self.supporting_quotes is None:
            self.supporting_quotes = []

class PatternBasedAdverseEventExtractor:
    """Extract adverse events using pattern matching and text analysis"""
    
    def __init__(self):
        self.ae_patterns = {
            'any_grade_ae': [
                r'adverse\s+events?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)%',
                r'([0-9]+(?:\.[0-9]+)?)%\s+adverse\s+events?',
                r'([0-9]+(?:\.[0-9]+)?)%\s+of\s+patients?\s+experienced\s+adverse\s+events?'
            ],
            'grade_3_4_ae': [
                r'grade\s+[34]\s+adverse\s+events?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)%',
                r'([0-9]+(?:\.[0-9]+)?)%\s+grade\s+[34]\s+adverse\s+events?',
                r'grade\s+[34]\s+toxicities?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)%'
            ],
            'serious_ae': [
                r'serious\s+adverse\s+events?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)%',
                r'([0-9]+(?:\.[0-9]+)?)%\s+serious\s+adverse\s+events?',
                r'SAEs?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)%'
            ],
            'treatment_related_ae': [
                r'treatment[- ]related\s+adverse\s+events?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)%',
                r'treatment[- ]emergent\s+adverse\s+events?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)%'
            ],
            'discontinuation': [
                r'discontinuation\s+due\s+to\s+adverse\s+events?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)%',
                r'([0-9]+(?:\.[0-9]+)?)%\s+discontinuation\s+due\s+to\s+adverse\s+events?'
            ],
            'dose_reduction': [
                r'dose\s+reduction\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)%',
                r'([0-9]+(?:\.[0-9]+)?)%\s+dose\s+reduction'
            ]
        }
        
        # Common hematologic and non-hematologic AEs
        self.hematologic_ae_keywords = [
            'neutropenia', 'thrombocytopenia', 'anemia', 'leukopenia', 'pancytopenia',
            'febrile neutropenia', 'cytopenia', 'myelosuppression'
        ]
        
        self.non_hematologic_ae_keywords = [
            'nausea', 'vomiting', 'diarrhea', 'fatigue', 'fever', 'infection',
            'pneumonia', 'sepsis', 'rash', 'pruritus', 'headache', 'dizziness',
            'constipation', 'anorexia', 'mucositis', 'dyspnea', 'cough'
        ]
    
    def extract_adverse_events(self, study_data: Dict[str, Any], full_text: str = None) -> AdverseEventData:
        """Extract adverse event data from study using pattern matching"""
        
        # Create base adverse event data object
        ae_data = AdverseEventData(
            pmid=study_data.get('pmid', ''),
            citation=study_data.get('citation', ''),
            url=study_data.get('url', '')
        )
        
        # Use available text content
        text_content = full_text or study_data.get('abstract', '') or study_data.get('key_findings', '')
        
        if not text_content:
            return ae_data
        
        # Extract overall AE rates
        ae_data.any_grade_ae_rate = self._extract_rate(text_content, self.ae_patterns['any_grade_ae'])
        ae_data.grade_3_4_ae_rate = self._extract_rate(text_content, self.ae_patterns['grade_3_4_ae'])
        ae_data.serious_ae_rate = self._extract_rate(text_content, self.ae_patterns['serious_ae'])
        ae_data.treatment_related_ae_rate = self._extract_rate(text_content, self.ae_patterns['treatment_related_ae'])
        ae_data.discontinuation_rate = self._extract_rate(text_content, self.ae_patterns['discontinuation'])
        ae_data.dose_reduction_rate = self._extract_rate(text_content, self.ae_patterns['dose_reduction'])
        
        # Extract specific AEs
        ae_data.hematologic_ae = self._extract_specific_ae(text_content, self.hematologic_ae_keywords)
        ae_data.non_hematologic_ae = self._extract_specific_ae(text_content, self.non_hematologic_ae_keywords)
        
        # Extract sample size information
        ae_data.total_patients = self._extract_sample_size(text_content)
        
        # Collect supporting quotes
        ae_data.supporting_quotes = self._extract_supporting_quotes(text_content)
        
        # Determine data source location
        ae_data.data_source_location = self._determine_data_source(study_data)
        
        # Calculate confidence based on data found
        ae_data.extraction_confidence = self._calculate_confidence(ae_data)
        
        return ae_data
    
    def _extract_rate(self, text: str, patterns: List[str]) -> Optional[float]:
        """Extract percentage rate using patterns"""
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return float(matches[0])
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_specific_ae(self, text: str, keywords: List[str]) -> Optional[Dict[str, float]]:
        """Extract specific adverse events with rates"""
        ae_dict = {}
        
        for keyword in keywords:
            # Look for patterns like "neutropenia (45.2%)" or "45.2% neutropenia"
            patterns = [
                rf'{keyword}\s*[\(\[]\s*([0-9]+(?:\.[0-9]+)?)%\s*[\)\]]',
                rf'([0-9]+(?:\.[0-9]+)?)%\s+{keyword}',
                rf'{keyword}\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)%'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    try:
                        rate = float(matches[0])
                        ae_dict[keyword] = rate
                        break
                    except (ValueError, IndexError):
                        continue
        
        return ae_dict if ae_dict else None
    
    def _extract_sample_size(self, text: str) -> Optional[int]:
        """Extract total patient sample size"""
        patterns = [
            r'(\d+)\s+patients?',
            r'(\d+)\s+subjects?',
            r'(\d+)\s+individuals?',
            r'n\s*=\s*(\d+)',
            r'sample\s+size\s+of\s+(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_supporting_quotes(self, text: str) -> List[str]:
        """Extract supporting quotes about adverse events"""
        quotes = []
        
        # Look for sentences containing adverse event information
        sentences = re.split(r'[.!?]+', text)
        
        ae_keywords = ['adverse event', 'toxicity', 'side effect', 'safety', 'grade', 'neutropenia', 'thrombocytopenia']
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(keyword in sentence.lower() for keyword in ae_keywords):
                quotes.append(sentence)
        
        return quotes[:5]  # Limit to 5 quotes
    
    def _determine_data_source(self, study_data: Dict[str, Any]) -> str:
        """Determine the source of the data"""
        if study_data.get('pmcid'):
            return "PMC Full Text"
        elif study_data.get('abstract'):
            return "Abstract"
        elif study_data.get('key_findings'):
            return "Key Findings"
        else:
            return "Unknown"
    
    def _calculate_confidence(self, ae_data: AdverseEventData) -> float:
        """Calculate confidence score based on data found"""
        confidence = 0.0
        
        # Base confidence for having any data
        if ae_data.any_grade_ae_rate or ae_data.grade_3_4_ae_rate or ae_data.serious_ae_rate:
            confidence += 0.3
        
        # Additional confidence for specific AEs
        if ae_data.hematologic_ae or ae_data.non_hematologic_ae:
            confidence += 0.2
        
        # Confidence for sample size
        if ae_data.total_patients:
            confidence += 0.1
        
        # Confidence for supporting quotes
        if ae_data.supporting_quotes:
            confidence += 0.1
        
        # Confidence for data source
        if ae_data.data_source_location in ["PMC Full Text", "Abstract"]:
            confidence += 0.1
        
        # Additional confidence for multiple data points
        data_points = sum([
            ae_data.any_grade_ae_rate is not None,
            ae_data.grade_3_4_ae_rate is not None,
            ae_data.serious_ae_rate is not None,
            ae_data.treatment_related_ae_rate is not None,
            ae_data.hematologic_ae is not None,
            ae_data.non_hematologic_ae is not None
        ])
        
        confidence += min(0.2, data_points * 0.05)
        
        return min(1.0, confidence)

def load_study_data(file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load the study data"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def main():
    """Main function to extract adverse events from PubMed papers"""
    
    # Load the PubMed papers
    input_file = 'pubmed_azacitidine_cmml.json'
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found. Please run fetch_pubmed_papers.py first.")
        return
    
    study_data = load_study_data(input_file)
    
    # Initialize extractor
    extractor = PatternBasedAdverseEventExtractor()
    
    # Extract adverse events for each drug
    all_adverse_events = {}
    
    for drug_name, studies in study_data.items():
        print(f"\nProcessing {drug_name} studies...")
        drug_adverse_events = []
        
        for i, study in enumerate(studies):
            print(f"  Processing study {i+1}/{len(studies)}: PMID {study.get('pmid', 'N/A')}")
            
            # Get text content (abstract or key findings)
            text_content = study.get('abstract', '') or study.get('key_findings', '')
            
            # Extract adverse events
            ae_data = extractor.extract_adverse_events(study, text_content)
            
            # Add drug information
            ae_data.drug = drug_name
            
            drug_adverse_events.append(asdict(ae_data))
        
        all_adverse_events[drug_name] = drug_adverse_events
    
    # Save results
    output_file = 'adverse_event_demo.json'
    with open(output_file, 'w') as f:
        json.dump(all_adverse_events, f, indent=2)
    
    print(f"\nAdverse event extraction completed. Results saved to {output_file}")
    
    # Print summary
    total_studies = sum(len(studies) for studies in all_adverse_events.values())
    print(f"Total studies processed: {total_studies}")
    
    for drug_name, studies in all_adverse_events.items():
        studies_with_ae = sum(1 for study in studies if study.get('any_grade_ae_rate') is not None or 
                             study.get('grade_3_4_ae_rate') is not None or 
                             study.get('serious_ae_rate') is not None)
        print(f"{drug_name}: {studies_with_ae}/{len(studies)} studies with AE data")
        
        # Show some examples
        if studies_with_ae > 0:
            print(f"  Sample AE rates found:")
            for study in studies[:3]:  # Show first 3 studies
                if study.get('any_grade_ae_rate') or study.get('serious_ae_rate'):
                    print(f"    PMID {study['pmid']}: Any grade AE: {study.get('any_grade_ae_rate')}%, "
                          f"Serious AE: {study.get('serious_ae_rate')}%")

if __name__ == "__main__":
    main()
