#!/usr/bin/env python3
"""
LLM-based adverse event extraction that feeds whole research papers to GPT
and asks it to identify and extract all adverse event information
"""

import json
import os
import time
import requests
from typing import Dict, List, Optional, Any
import google.generativeai as genai
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
    
    # Additional fields for comprehensive AE data
    ae_summary: Optional[str] = None
    has_ae_data: bool = False
    
    def __post_init__(self):
        if self.supporting_quotes is None:
            self.supporting_quotes = []

class LLMAdverseEventExtractor:
    def __init__(self, gemini_api_key: str):
        """Initialize the LLM-based adverse event extractor with Gemini API"""
        self.gemini_api_key = gemini_api_key
        self.model = None
        
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self._initialize_model()
    
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
    
    def fetch_pmc_fulltext(self, pmcid: str) -> Optional[str]:
        """Try to fetch full text from PMC via E-utilities"""
        if not pmcid:
            return None
        
        # Normalize PMCID
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
            
            # Title
            title = root.find(".//article-title")
            if title is not None:
                text_parts.append(f"TITLE: {ET.tostring(title, encoding='unicode', method='text')}")
            
            # Abstract
            abstracts = root.findall(".//abstract")
            for abstract in abstracts:
                text_parts.append(f"ABSTRACT: {ET.tostring(abstract, encoding='unicode', method='text')}")
            
            # Introduction/Background
            intro_sections = root.findall(".//sec[@sec-type='intro']") + root.findall(".//sec[@sec-type='background']")
            for section in intro_sections:
                text_parts.append(f"INTRODUCTION: {ET.tostring(section, encoding='unicode', method='text')}")
            
            # Methods
            methods = root.findall(".//sec[@sec-type='methods']") + root.findall(".//sec[@sec-type='materials|methods']")
            for method in methods:
                text_parts.append(f"METHODS: {ET.tostring(method, encoding='unicode', method='text')}")
            
            # Results section
            results = root.findall(".//sec[@sec-type='results']")
            for result in results:
                text_parts.append(f"RESULTS: {ET.tostring(result, encoding='unicode', method='text')}")
            
            # Discussion
            discussion = root.findall(".//sec[@sec-type='discussion']") + root.findall(".//sec[@sec-type='conclusions']")
            for disc in discussion:
                text_parts.append(f"DISCUSSION: {ET.tostring(disc, encoding='unicode', method='text')}")
            
            # Safety/Adverse events sections (priority for AE extraction)
            safety_sections = root.findall(".//sec[contains(translate(title, 'SAFETY ADVERSE TOLERABILITY', 'safety adverse tolerability'), 'safety') or contains(translate(title, 'SAFETY ADVERSE TOLERABILITY', 'safety adverse tolerability'), 'adverse') or contains(translate(title, 'SAFETY ADVERSE TOLERABILITY', 'safety adverse tolerability'), 'tolerability')]")
            for section in safety_sections:
                text_parts.append(f"SAFETY/AE SECTION: {ET.tostring(section, encoding='unicode', method='text')}")
            
            # Tables (often contain AE data)
            tables = root.findall(".//table-wrap")
            for i, table in enumerate(tables[:5]):  # Limit to first 5 tables
                text_parts.append(f"TABLE {i+1}: {ET.tostring(table, encoding='unicode', method='text')}")
            
            full_text = '\n\n'.join(text_parts)
            if len(full_text) > 1000:  # Only return if we got substantial text
                return full_text
                
        except Exception as e:
            print(f"Error fetching PMC full text for {pmcid}: {e}")
        
        return None
    
    def extract_adverse_events(self, study_data: Dict[str, Any], full_text: str = None) -> AdverseEventData:
        """Extract adverse event data from study using LLM"""
        
        # Create base adverse event data object
        ae_data = AdverseEventData(
            pmid=study_data.get('pmid', ''),
            citation=study_data.get('citation', ''),
            url=study_data.get('url', '')
        )
        
        if not self.model:
            return ae_data
        
        # Get the best available text content
        text_content = self._get_best_text_content(study_data, full_text)
        
        if not text_content or len(text_content.strip()) < 100:
            return ae_data
        
        try:
            # Create comprehensive prompt for adverse event extraction
            prompt = self._create_comprehensive_ae_prompt(study_data, text_content)
            
            # Get response from LLM
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # Parse the LLM response
                parsed_data = self._parse_llm_response(response.text)
                
                # Update the adverse event data
                for key, value in parsed_data.items():
                    if hasattr(ae_data, key):
                        setattr(ae_data, key, value)
                
                # Set flags
                ae_data.has_ae_data = self._has_meaningful_ae_data(ae_data)
                ae_data.extraction_confidence = parsed_data.get('extraction_confidence', 0.0)
                ae_data.data_source_location = self._determine_data_source(study_data, full_text)
            
        except Exception as e:
            print(f"Error extracting adverse events for PMID {ae_data.pmid}: {e}")
        
        return ae_data
    
    def _get_best_text_content(self, study_data: Dict[str, Any], full_text: str = None) -> str:
        """Get the best available text content for analysis"""
        if full_text:
            return full_text
        
        # Try to get PMC full text if available
        pmcid = study_data.get('pmcid')
        if pmcid:
            print(f"    Attempting to fetch full text from PMC: {pmcid}")
            pmc_text = self.fetch_pmc_fulltext(pmcid)
            if pmc_text:
                print(f"    Successfully fetched {len(pmc_text)} characters from PMC")
                return pmc_text
        
        # Fallback to available content
        content_parts = []
        
        if study_data.get('title'):
            content_parts.append(f"TITLE: {study_data['title']}")
        
        if study_data.get('abstract'):
            content_parts.append(f"ABSTRACT: {study_data['abstract']}")
        
        if study_data.get('key_findings'):
            content_parts.append(f"KEY FINDINGS: {study_data['key_findings']}")
        
        return '\n\n'.join(content_parts)
    
    def _create_comprehensive_ae_prompt(self, study_data: Dict[str, Any], text_content: str) -> str:
        """Create a comprehensive prompt for adverse event extraction"""
        
        prompt = f"""
You are a medical data extraction specialist with expertise in adverse events (AEs) from clinical studies. 

TASK: Analyze the following research paper and extract ALL adverse event information.

STUDY INFORMATION:
- PMID: {study_data.get('pmid', 'N/A')}
- Citation: {study_data.get('citation', 'N/A')}

FULL STUDY CONTENT:
{text_content[:100000]}  # Limit to avoid token limits

INSTRUCTIONS:
1. Read the ENTIRE study content carefully
2. Look for ANY mention of adverse events, side effects, toxicities, safety issues, complications, or treatment-related problems
3. Extract specific percentages, patient counts, and descriptions
4. Pay special attention to safety sections, results, tables, and discussion sections
5. Include both overall rates and specific adverse events
6. Note any treatment discontinuations, dose reductions, or modifications due to AEs

EXTRACTION REQUIREMENTS:
Extract and return the following information in JSON format:

{{
    "has_ae_data": <true if ANY adverse event information is found, false otherwise>,
    "ae_summary": "<brief summary of adverse events found in the study>",
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
    "total_patients": <total number of patients in the study, or null if not clear>,
    "patients_with_ae": <number of patients who experienced AEs, or null if not reported>,
    "supporting_quotes": [
        "<exact quote from text showing AE information>",
        "<another exact quote>",
        ...
    ],
    "extraction_confidence": <float between 0.0 and 1.0 - how confident you are in the extraction>
}}

IMPORTANT GUIDELINES:
- Set "has_ae_data" to true if you find ANY adverse event information, even if minimal
- For hematologic_ae, include: neutropenia, thrombocytopenia, anemia, leukopenia, etc.
- For non_hematologic_ae, include: nausea, vomiting, fatigue, infection, fever, etc.
- Extract exact percentages when available (e.g., "nausea in 25% of patients" → "nausea": 25.0)
- Include exact quotes as supporting evidence
- Be thorough - adverse events can be mentioned anywhere in the paper
- If percentages are not given but patient counts are, calculate percentages if total is known
- Look for phrases like: "adverse events", "side effects", "toxicity", "safety", "tolerability"

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
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            parsed_data = json.loads(response_text)
            
            # Validate and clean the data
            cleaned_data = {}
            for key, value in parsed_data.items():
                if key == 'has_ae_data':
                    cleaned_data[key] = bool(value) if value is not None else False
                elif key == 'ae_summary':
                    cleaned_data[key] = str(value) if value else None
                elif key in ['any_grade_ae_rate', 'grade_3_4_ae_rate', 'serious_ae_rate', 
                            'treatment_related_ae_rate', 'discontinuation_rate', 'dose_reduction_rate']:
                    if isinstance(value, (int, float)) and value >= 0:
                        cleaned_data[key] = float(value)
                elif key in ['total_patients', 'patients_with_ae']:
                    if isinstance(value, (int, float)) and value >= 0:
                        cleaned_data[key] = int(value)
                elif key in ['hematologic_ae', 'non_hematologic_ae']:
                    if isinstance(value, dict):
                        cleaned_ae_dict = {}
                        for ae_name, ae_rate in value.items():
                            if isinstance(ae_rate, (int, float)) and ae_rate >= 0:
                                cleaned_ae_dict[ae_name.lower()] = float(ae_rate)
                        if cleaned_ae_dict:
                            cleaned_data[key] = cleaned_ae_dict
                elif key == 'supporting_quotes':
                    if isinstance(value, list):
                        quotes = [str(quote).strip() for quote in value if quote]
                        if quotes:
                            cleaned_data[key] = quotes[:10]  # Limit to 10 quotes
                elif key == 'extraction_confidence':
                    if isinstance(value, (int, float)):
                        cleaned_data[key] = min(1.0, max(0.0, float(value)))
            
            return cleaned_data
            
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            print(f"Response text: {response_text[:500]}...")
            return {'has_ae_data': False}
        except Exception as e:
            print(f"Error processing LLM response: {e}")
            return {'has_ae_data': False}
    
    def _has_meaningful_ae_data(self, ae_data: AdverseEventData) -> bool:
        """Check if the extracted data contains meaningful AE information"""
        return any([
            ae_data.any_grade_ae_rate is not None,
            ae_data.grade_3_4_ae_rate is not None,
            ae_data.serious_ae_rate is not None,
            ae_data.treatment_related_ae_rate is not None,
            ae_data.hematologic_ae is not None,
            ae_data.non_hematologic_ae is not None,
            ae_data.discontinuation_rate is not None,
            ae_data.dose_reduction_rate is not None,
            ae_data.supporting_quotes
        ])
    
    def _determine_data_source(self, study_data: Dict[str, Any], full_text: str = None) -> str:
        """Determine the source of the data"""
        if full_text and len(full_text) > 5000:
            return "PMC Full Text"
        elif study_data.get('pmcid'):
            return "PMC (partial)"
        elif study_data.get('abstract'):
            return "Abstract"
        else:
            return "Limited data"

def load_study_data(file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load the study data"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def main():
    """Main function to extract adverse events from studies using LLM"""
    
    # Get API key from environment
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    if not gemini_api_key:
        print("GEMINI_API_KEY not set. Please set the environment variable.")
        print("Example: export GEMINI_API_KEY='your_api_key_here'")
        return
    
    # Initialize extractor
    try:
        extractor = LLMAdverseEventExtractor(gemini_api_key)
        print("Successfully initialized LLM adverse event extractor")
    except Exception as e:
        print(f"Failed to initialize extractor: {e}")
        return
    
    # Load study data
    input_file = 'pubmed_azacitidine_cmml.json'
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found. Please run fetch_pubmed_papers.py first.")
        return
    
    study_data = load_study_data(input_file)
    
    # Extract adverse events for each drug
    all_adverse_events = {}
    
    for drug_name, studies in study_data.items():
        print(f"\nProcessing {drug_name} studies...")
        drug_adverse_events = []
        
        # Limit to first 10 studies for testing (remove this limit for full processing)
        studies_to_process = studies[:10]
        print(f"Processing first {len(studies_to_process)} studies for testing...")
        
        for i, study in enumerate(studies_to_process):
            print(f"  Processing study {i+1}/{len(studies_to_process)}: PMID {study.get('pmid', 'N/A')}")
            
            # Extract adverse events using LLM
            ae_data = extractor.extract_adverse_events(study)
            
            # Add drug information
            ae_data.drug = drug_name
            
            drug_adverse_events.append(asdict(ae_data))
            
            # Show progress
            if ae_data.has_ae_data:
                print(f"    ✓ Found adverse event data (confidence: {ae_data.extraction_confidence:.2f})")
                if ae_data.ae_summary:
                    print(f"    Summary: {ae_data.ae_summary[:100]}...")
            else:
                print(f"    ○ No adverse event data found")
            
            # Add delay to avoid rate limiting
            time.sleep(2)
        
        all_adverse_events[drug_name] = drug_adverse_events
    
    # Save results
    output_file = 'adverse_event.json'
    with open(output_file, 'w') as f:
        json.dump(all_adverse_events, f, indent=2)
    
    print(f"\nAdverse event extraction completed. Results saved to {output_file}")
    
    # Print comprehensive summary
    total_studies = sum(len(studies) for studies in all_adverse_events.values())
    total_with_ae = sum(sum(1 for study in studies if study.get('has_ae_data', False)) 
                       for studies in all_adverse_events.values())
    
    print(f"\nSUMMARY:")
    print(f"Total studies processed: {total_studies}")
    print(f"Studies with AE data: {total_with_ae}/{total_studies} ({total_with_ae/total_studies*100:.1f}%)")
    
    for drug_name, studies in all_adverse_events.items():
        studies_with_ae = sum(1 for study in studies if study.get('has_ae_data', False))
        print(f"\n{drug_name}: {studies_with_ae}/{len(studies)} studies with AE data")
        
        # Show examples of found AE data
        examples = [s for s in studies if s.get('has_ae_data', False)][:3]
        for example in examples:
            print(f"  PMID {example['pmid']}: {example.get('ae_summary', 'N/A')[:80]}...")

if __name__ == "__main__":
    main()
