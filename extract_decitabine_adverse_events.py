#!/usr/bin/env python3
"""
Extract adverse events from decitabine CMML papers with abstracts
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

def extract_decitabine_adverse_events():
    # Load the decitabine papers with abstracts
    with open('Decitabine_extracted_with_abstracts.json', 'r') as f:
        papers = json.load(f)
    
    # Filter papers that have abstracts
    papers_with_abstracts = [p for p in papers if p.get('abstract')]
    
    print(f"Extracting adverse events from {len(papers_with_abstracts)} decitabine papers with abstracts...")
    
    extracted_papers = []
    
    for i, paper in enumerate(papers_with_abstracts):
        pmid = paper['pmid']
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        citation = paper.get('citation', '')
        
        print(f"\n{i+1}. Processing PMID {pmid}: {title[:60] if title else 'No title'}...")
        
        # Create the prompt for extraction
        prompt = f"""
You are a medical data extraction specialist. Extract adverse event data from this CMML paper that focuses on DECITABINE treatment.

Paper Information:
- PMID: {pmid}
- Title: {title}
- Abstract: {abstract}
- Citation: {citation}

Extract ONLY adverse events specifically mentioned for DECITABINE treatment in CMML patients:

ADVERSE EVENTS TO EXTRACT:
1. Any adverse events mentioned (list all)
2. Grade 3-4 adverse events (if specified)
3. Serious adverse events (SAE) - percentage or count
4. Most common adverse events
5. Treatment discontinuation due to adverse events
6. Deaths related to treatment

IMPORTANT: 
- Only extract data for DECITABINE treatment, not other drugs
- If data is not available, use null
- Be precise with numbers and units
- Focus on CMML-specific decitabine treatment data
- For adverse events, provide specific percentages or counts when available

Return the data in this exact JSON format:
{{
    "pmid": "{pmid}",
    "citation": "{citation}",
    "title": "{title}",
    "abstract": "{abstract}",
    "has_adverse_event_data": true/false,
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
                has_data = extracted_data.get('has_adverse_event_data', False)
                if has_data:
                    ae = extracted_data.get('adverse_events', {}).get('any_adverse_events', '')
                    print(f"   ✓ Adverse events found: {ae[:100]}...")
                else:
                    print(f"   ✗ No adverse events found")
                
            except json.JSONDecodeError as e:
                print(f"   ✗ JSON parsing error: {e}")
                # Add a basic entry
                extracted_papers.append({
                    "pmid": pmid,
                    "citation": citation,
                    "title": title,
                    "abstract": abstract,
                    "has_adverse_event_data": False,
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
                "has_adverse_event_data": False,
                "adverse_events": {},
                "extraction_notes": f"API error: {e}"
            })
        
        time.sleep(2)  # Rate limiting
    
    # Save the extracted data
    output_file = 'Decitabine_adverse_events_extracted.json'
    with open(output_file, 'w') as f:
        json.dump(extracted_papers, f, indent=2)
    
    print(f"\n💾 Saved extracted adverse events to {output_file}")
    
    # Summary statistics
    total_papers = len(extracted_papers)
    papers_with_ae = sum(1 for p in extracted_papers if p.get('has_adverse_event_data', False))
    
    print(f"\n📊 Extraction Summary:")
    print(f"Total papers processed: {total_papers}")
    print(f"Papers with adverse event data: {papers_with_ae}")
    print(f"Success rate: {papers_with_ae/total_papers*100:.1f}%")

if __name__ == "__main__":
    extract_decitabine_adverse_events()
