import json
import os
import time
import requests
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

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
    hematologic_ae: Optional[Dict[str, float]] = None  # e.g., {"neutropenia": 45.2, "thrombocytopenia": 32.1}
    non_hematologic_ae: Optional[Dict[str, float]] = None  # e.g., {"nausea": 25.0, "fatigue": 30.5}
    
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

class AdverseEventExtractor:
    def __init__(self, gemini_api_key: str):
        """Initialize the adverse event extractor with Gemini API"""
        self.gemini_api_key = gemini_api_key
        self.model = None
        
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self._initialize_model()
    
    def fetch_pmc_fulltext(self, pmcid: str) -> Optional[str]:
        """Try to fetch full text from PMC via E-utilities (XML) and fallback to HTML scraping."""
        if not pmcid:
            return None
        
        # Normalize, accept forms like 'PMC1234567' or just the digits
        pmc_id_value = pmcid.replace('PMC', '')
        
        try:
            # Try efetch for PMC NXML
            efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            params = {
                'db': 'pmc',
                'id': pmc_id_value,
                'retmode': 'xml',
                'rettype': 'xml'
            }
            
            response = requests.get(efetch_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML and extract text
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Extract text from various sections
            text_parts = []
            
            # Abstract
            abstracts = root.findall(".//abstract")
            for abstract in abstracts:
                text_parts.append(ET.tostring(abstract, encoding='unicode', method='text'))
            
            # Body text
            body = root.find(".//body")
            if body is not None:
                text_parts.append(ET.tostring(body, encoding='unicode', method='text'))
            
            # Results section specifically
            results = root.findall(".//sec[@sec-type='results']")
            for result in results:
                text_parts.append(ET.tostring(result, encoding='unicode', method='text'))
            
            # Safety/Adverse events sections
            safety_sections = root.findall(".//sec[contains(translate(title, 'SAFETY', 'safety'), 'safety') or contains(translate(title, 'ADVERSE', 'adverse'), 'adverse')]")
            for section in safety_sections:
                text_parts.append(ET.tostring(section, encoding='unicode', method='text'))
            
            full_text = '\n\n'.join(text_parts)
            if full_text.strip():
                return full_text
            
        except Exception as e:
            print(f"Error fetching PMC full text for {pmcid}: {e}")
        
        # Fallback: try HTML scraping
        try:
            url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id_value}/"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Simple text extraction from HTML
            import re
            # Remove HTML tags and extract text
            text = re.sub(r'<[^>]+>', ' ', response.text)
            text = re.sub(r'\s+', ' ', text)
            
            if len(text) > 1000:  # Only return if we got substantial text
                return text
                
        except Exception as e:
            print(f"Error scraping HTML for {pmcid}: {e}")
        
        return None
    
    def _initialize_model(self):
        """Initialize the Gemini model"""
        model_names = [
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-pro'
        ]
        
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                print(f"Successfully initialized {model_name}")
                break
            except Exception as e:
                print(f"Failed to initialize {model_name}: {e}")
                continue
        
        if not self.model:
            raise Exception("Could not initialize any Gemini model")
    
    def extract_adverse_events(self, study_data: Dict[str, Any], full_text: str = None) -> AdverseEventData:
        """Extract adverse event data from study using LLM"""
        
        # Create base adverse event data object
        ae_data = AdverseEventData(
            pmid=study_data.get('pmid', ''),
            citation=study_data.get('citation', ''),
            url=study_data.get('url', '')
        )
        
        if not self.model or not full_text:
            return ae_data
        
        try:
            # Create prompt for adverse event extraction
            prompt = self._create_ae_extraction_prompt(study_data, full_text)
            
            # Get response from LLM
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # Parse the LLM response
                parsed_data = self._parse_llm_response(response.text)
                
                # Update the adverse event data
                for key, value in parsed_data.items():
                    if hasattr(ae_data, key):
                        setattr(ae_data, key, value)
                
                ae_data.extraction_confidence = parsed_data.get('extraction_confidence', 0.0)
            
        except Exception as e:
            print(f"Error extracting adverse events for PMID {ae_data.pmid}: {e}")
        
        return ae_data
    
    def _create_ae_extraction_prompt(self, study_data: Dict[str, Any], full_text: str) -> str:
        """Create a comprehensive prompt for adverse event extraction"""
        
        prompt = f"""
You are a medical data extraction specialist. Extract comprehensive adverse event (AE) information from the following clinical study.

STUDY INFORMATION:
- PMID: {study_data.get('pmid', 'N/A')}
- Citation: {study_data.get('citation', 'N/A')}
- Drug: {study_data.get('drug', 'N/A')}

STUDY CONTENT:
{full_text[:50000]}  # Limit to first 50k characters to avoid token limits

EXTRACTION TASK:
Extract all adverse event data and return it in the following JSON format:

{{
    "any_grade_ae_rate": <percentage as float, or null if not reported>,
    "grade_3_4_ae_rate": <percentage as float, or null if not reported>,
    "serious_ae_rate": <percentage as float, or null if not reported>,
    "treatment_related_ae_rate": <percentage as float, or null if not reported>,
    "hematologic_ae": {{
        "<ae_name>": <percentage as float>,
        ...
    }},
    "non_hematologic_ae": {{
        "<ae_name>": <percentage as float>,
        ...
    }},
    "discontinuation_rate": <percentage as float, or null if not reported>,
    "dose_reduction_rate": <percentage as float, or null if not reported>,
    "total_patients": <integer, or null if not reported>,
    "patients_with_ae": <integer, or null if not reported>,
    "supporting_quotes": [
        "<exact quote from text>",
        ...
    ],
    "data_source_location": "<section where AE data was found: Abstract, Methods, Results, etc.>",
    "extraction_confidence": <float between 0.0 and 1.0>
}}

INSTRUCTIONS:
1. Extract ALL adverse event data mentioned in the study
2. Include both overall rates and specific adverse events
3. Provide exact quotes from the text as supporting evidence
4. Specify the section where the data was found
5. Rate your confidence in the extraction (1.0 = very confident, 0.0 = not confident)
6. If a value is not reported, use null
7. For percentages, convert to decimal format (e.g., 25% = 25.0)
8. Focus on CMML-specific adverse events when available

Return ONLY the JSON object, no additional text.
"""
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the LLM response and extract structured data"""
        try:
            # Clean the response text
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            parsed_data = json.loads(response_text)
            
            # Validate and clean the data
            cleaned_data = {}
            for key, value in parsed_data.items():
                if value is not None:
                    if key in ['any_grade_ae_rate', 'grade_3_4_ae_rate', 'serious_ae_rate', 
                              'treatment_related_ae_rate', 'discontinuation_rate', 'dose_reduction_rate']:
                        # Ensure percentage values are floats
                        if isinstance(value, (int, float)):
                            cleaned_data[key] = float(value)
                    elif key in ['total_patients', 'patients_with_ae']:
                        # Ensure integer values
                        if isinstance(value, (int, float)):
                            cleaned_data[key] = int(value)
                    elif key in ['hematologic_ae', 'non_hematologic_ae']:
                        # Ensure AE dictionaries have float values
                        if isinstance(value, dict):
                            cleaned_ae_dict = {}
                            for ae_name, ae_rate in value.items():
                                if isinstance(ae_rate, (int, float)):
                                    cleaned_ae_dict[ae_name] = float(ae_rate)
                            cleaned_data[key] = cleaned_ae_dict
                    elif key == 'supporting_quotes':
                        # Ensure quotes are strings
                        if isinstance(value, list):
                            cleaned_data[key] = [str(quote) for quote in value if quote]
                    elif key == 'data_source_location':
                        cleaned_data[key] = str(value)
                    elif key == 'extraction_confidence':
                        if isinstance(value, (int, float)):
                            cleaned_data[key] = min(1.0, max(0.0, float(value)))
            
            return cleaned_data
            
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response: {e}")
            return {}
        except Exception as e:
            print(f"Error processing LLM response: {e}")
            return {}

def load_study_data(file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load the detailed outcomes data"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Remove metadata and return only drug data
    if 'extraction_metadata' in data:
        del data['extraction_metadata']
    
    return data

def get_full_text_for_study(study_data: Dict[str, Any], extractor: AdverseEventExtractor) -> str:
    """Get the full text content for a study"""
    content_parts = []
    
    # Try to get PMC full text first
    pmcid = study_data.get('pmcid')
    if pmcid:
        print(f"    Attempting to fetch full text from PMC: {pmcid}")
        full_text = extractor.fetch_pmc_fulltext(pmcid)
        if full_text:
            print(f"    Successfully fetched {len(full_text)} characters from PMC")
            return full_text
        else:
            print(f"    Failed to fetch PMC full text, using available data")
    
    # Fallback to available fields
    if study_data.get('key_findings'):
        content_parts.append(f"Key Findings: {study_data['key_findings']}")
    
    if study_data.get('study_design'):
        content_parts.append(f"Study Design: {study_data['study_design']}")
    
    if study_data.get('patient_population'):
        content_parts.append(f"Patient Population: {study_data['patient_population']}")
    
    if study_data.get('treatment_details'):
        content_parts.append(f"Treatment Details: {study_data['treatment_details']}")
    
    if study_data.get('supporting_quotes'):
        content_parts.append(f"Supporting Quotes: {' '.join(study_data['supporting_quotes'])}")
    
    return '\n\n'.join(content_parts)

def main():
    """Main function to extract adverse events from all studies"""
    
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
    
    # Extract adverse events for each drug
    all_adverse_events = {}
    
    for drug_name, studies in study_data.items():
        print(f"\nProcessing {drug_name} studies...")
        drug_adverse_events = []
        
        for i, study in enumerate(studies):
            print(f"  Processing study {i+1}/{len(studies)}: PMID {study.get('pmid', 'N/A')}")
            
            # Get full text content
            full_text = get_full_text_for_study(study, extractor)
            
            # Extract adverse events
            ae_data = extractor.extract_adverse_events(study, full_text)
            
            # Add drug information
            ae_data.drug = drug_name
            
            drug_adverse_events.append(asdict(ae_data))
            
            # Add delay to avoid rate limiting
            time.sleep(1)
        
        all_adverse_events[drug_name] = drug_adverse_events
    
    # Save results
    output_file = 'adverse_event.json'
    with open(output_file, 'w') as f:
        json.dump(all_adverse_events, f, indent=2)
    
    print(f"\nAdverse event extraction completed. Results saved to {output_file}")
    
    # Print summary
    total_studies = sum(len(studies) for studies in all_adverse_events.values())
    print(f"Total studies processed: {total_studies}")
    
    for drug_name, studies in all_adverse_events.items():
        studies_with_ae = sum(1 for study in studies if study.get('any_grade_ae_rate') is not None)
        print(f"{drug_name}: {studies_with_ae}/{len(studies)} studies with AE data")

if __name__ == "__main__":
    main()
