#!/usr/bin/env python3
"""
Extract efficacy data from comprehensive hydroxyurea CMML papers
"""

import os
import json
import time
import google.generativeai as genai
from datetime import datetime

# Configure Gemini API
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("Error: GEMINI_API_KEY environment variable not set")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_efficacy_data():
    # Load the detailed papers
    with open('pubmed_hydroxyurea_cmml_detailed.json', 'r') as f:
        papers = json.load(f)
    
    print(f"Extracting efficacy and adverse event data from {len(papers)} hydroxyurea CMML papers...")
    
    extracted_papers = []
    
    for i, paper in enumerate(papers):
        pmid = paper['pmid']
        title = paper['title']
        abstract = paper.get('abstract', '')
        citation = paper.get('citation', '')
        
        print(f"\n{i+1}. Processing PMID {pmid}: {title[:60]}...")
        
        # Create the prompt for extraction
        prompt = f"""
You are a medical data extraction specialist. Extract clinical efficacy and adverse event data from this CMML paper that specifically focuses on HYDROXYUREA treatment.

Paper Information:
- PMID: {pmid}
- Title: {title}
- Abstract: {abstract}
- Citation: {citation}

Extract ONLY the following data points if they are specifically mentioned for HYDROXYUREA treatment in CMML patients:

EFFICACY DATA:
1. Complete Response Rate (CR) - percentage
2. Overall Response Rate (ORR) - percentage  
3. Progression-Free Survival (PFS) - median in months
4. Overall Survival (OS) - median in months
5. Number of patients treated with hydroxyurea
6. Treatment duration/cycles

ADVERSE EVENTS:
7. Any adverse events mentioned (list all)
8. Grade 3-4 adverse events (if specified)
9. Serious adverse events (SAE) - percentage or count
10. Most common adverse events
11. Treatment discontinuation due to adverse events
12. Deaths related to treatment

IMPORTANT: 
- Only extract data for HYDROXYUREA treatment, not other drugs
- If data is not available, use null
- Be precise with numbers and units
- Focus on CMML-specific hydroxyurea treatment data
- For adverse events, provide specific percentages or counts when available

Return the data in this exact JSON format:
{{
    "pmid": "{pmid}",
    "citation": "{citation}",
    "title": "{title}",
    "abstract": "{abstract}",
    "has_efficacy_data": true/false,
    "complete_response": number or null,
    "overall_response_rate": number or null,
    "progression_free_survival_median": number or null,
    "overall_survival_median": number or null,
    "number_of_patients": number or null,
    "treatment_cycles": number or null,
    "adverse_events": {{
        "any_adverse_events": "text description or null",
        "grade_3_4_events": "text description or null",
        "serious_adverse_events": "percentage or count or null",
        "most_common_events": ["list of events or null"],
        "treatment_discontinuation": "percentage or count or null",
        "treatment_related_deaths": "count or null"
    }},
    "extraction_notes": "brief notes about what was found"
}}
"""

        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Try to parse the JSON response
            try:
                # Clean up the response to extract JSON
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    json_str = response_text[json_start:json_end].strip()
                elif '```' in response_text:
                    json_start = response_text.find('```') + 3
                    json_end = response_text.find('```', json_start)
                    json_str = response_text[json_start:json_end].strip()
                else:
                    json_str = response_text
                
                extracted_data = json.loads(json_str)
                
                # Add the extracted data to our list
                extracted_papers.append(extracted_data)
                
                # Print summary
                has_data = extracted_data.get('has_efficacy_data', False)
                if has_data:
                    cr = extracted_data.get('complete_response')
                    orr = extracted_data.get('overall_response_rate')
                    pfs = extracted_data.get('progression_free_survival_median')
                    os_val = extracted_data.get('overall_survival_median')
                    ae = extracted_data.get('adverse_events', {})
                    print(f"   ✓ Efficacy data found: CR={cr}%, ORR={orr}%, PFS={pfs}m, OS={os_val}m")
                    if ae.get('any_adverse_events'):
                        print(f"   ✓ Adverse events: {ae.get('any_adverse_events')[:100]}...")
                else:
                    print(f"   ✗ No efficacy data found")
                
            except json.JSONDecodeError as e:
                print(f"   ✗ JSON parsing error: {e}")
                print(f"   Response: {response_text[:200]}...")
                # Add a basic entry
                extracted_papers.append({
                    "pmid": pmid,
                    "citation": citation,
                    "title": title,
                    "abstract": abstract,
                    "has_efficacy_data": False,
                    "adverse_events": {},
                    "extraction_notes": f"JSON parsing error: {e}"
                })
                
        except Exception as e:
            print(f"   ✗ API error: {e}")
            # Add a basic entry
            extracted_papers.append({
                "pmid": pmid,
                "citation": citation,
                "title": title,
                "abstract": abstract,
                "has_efficacy_data": False,
                "adverse_events": {},
                "extraction_notes": f"API error: {e}"
            })
        
        time.sleep(2)  # Rate limiting
    
    # Save the extracted data
    output_file = 'Hydroxyurea_extracted_comprehensive.json'
    with open(output_file, 'w') as f:
        json.dump(extracted_papers, f, indent=2)
    
    print(f"\n💾 Saved extracted data to {output_file}")
    
    # Summary statistics
    total_papers = len(extracted_papers)
    papers_with_data = sum(1 for p in extracted_papers if p.get('has_efficacy_data', False))
    papers_with_ae = sum(1 for p in extracted_papers if p.get('adverse_events', {}).get('any_adverse_events'))
    
    print(f"\n📊 Extraction Summary:")
    print(f"Total papers processed: {total_papers}")
    print(f"Papers with efficacy data: {papers_with_data}")
    print(f"Papers with adverse event data: {papers_with_ae}")
    print(f"Success rate: {papers_with_data/total_papers*100:.1f}%")

if __name__ == "__main__":
    extract_efficacy_data()
