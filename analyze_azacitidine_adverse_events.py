#!/usr/bin/env python3
"""
Analyze and count adverse events from azacitidine CMML papers
"""
import json
import re
from collections import defaultdict

def analyze_azacitidine_adverse_events():
    """Analyze adverse events from azacitidine papers"""
    print("Loading azacitidine adverse events data...")
    
    # Load the azacitidine adverse events data
    with open('azacitidine_adverse_events_extracted.json', 'r') as f:
        data = json.load(f)
    
    print(f"Found {len(data)} papers")
    
    # Filter papers with adverse event data
    papers_with_ae = [p for p in data if p.get('has_adverse_event_data', False)]
    print(f"Papers with adverse event data: {len(papers_with_ae)}")
    
    # Collect all adverse event data
    all_ae_data = []
    adverse_event_counts = defaultdict(lambda: {'papers': 0, 'patients': 0})
    
    for paper in papers_with_ae:
        pmid = paper.get('pmid', 'Unknown')
        citation = paper.get('citation', '')
        ae_data = paper.get('adverse_events', {})
        
        # Collect text from all AE fields
        ae_texts = []
        for field, value in ae_data.items():
            if value and value != 'null':
                if isinstance(value, list):
                    ae_texts.extend(value)
                else:
                    ae_texts.append(str(value))
        
        if ae_texts:
            all_ae_data.append({
                'pmid': pmid,
                'citation': citation,
                'ae_texts': ae_texts
            })
    
    print(f"Papers with extractable AE text: {len(all_ae_data)}")
    
    # Define common adverse events to look for (expanded list for azacitidine)
    ae_patterns = {
        'myelosuppression': r'myelosuppression|cytopenia|neutropenia|thrombocytopenia|anemia|leukopenia',
        'gastrointestinal': r'gastrointestinal|nausea|vomiting|diarrhea|abdominal|constipation|anorexia',
        'fatigue': r'fatigue|tiredness|weakness|asthenia',
        'infection': r'infection|sepsis|febrile|pneumonia|bacteremia',
        'fever': r'fever|pyrexia|hyperthermia',
        'skin': r'skin|rash|dermatitis|pruritus|erythema',
        'hepatotoxicity': r'hepatotoxicity|liver|hepatic|elevated.*liver|bilirubin|transaminase',
        'renal': r'renal|kidney|nephrotoxicity|creatinine|glomerular',
        'cardiac': r'cardiac|heart|arrhythmia|tachycardia|bradycardia|chest pain',
        'pulmonary': r'pulmonary|respiratory|dyspnea|shortness of breath|cough|pneumonitis',
        'neurological': r'neurological|neuropathy|headache|dizziness|confusion|seizure',
        'bleeding': r'bleeding|hemorrhage|petechiae|ecchymosis|epistaxis',
        'edema': r'edema|swelling|fluid retention|peripheral edema',
        'pain': r'pain|arthralgia|myalgia|bone pain',
        'dysgeusia': r'dysgeusia|taste|metallic taste',
        'insomnia': r'insomnia|sleep|somnolence',
        'anxiety': r'anxiety|depression|mood|psychiatric',
        'weight': r'weight loss|weight gain|appetite',
        'transfusion': r'transfusion|blood product|platelet|red blood cell',
        'dose_reduction': r'dose reduction|dose modification|dose adjustment',
        'discontinuation': r'discontinuation|withdrawal|stopped|halted',
        'death': r'death|mortality|fatal|lethal'
    }
    
    # Analyze each paper
    for paper_data in all_ae_data:
        pmid = paper_data['pmid']
        ae_texts = paper_data['ae_texts']
        
        # Combine all AE text for this paper
        combined_text = ' '.join(ae_texts).lower()
        
        # Check for each AE pattern
        for ae_type, pattern in ae_patterns.items():
            if re.search(pattern, combined_text, re.IGNORECASE):
                adverse_event_counts[ae_type]['papers'] += 1
                
                # Try to extract patient count from the text
                patient_match = re.search(r'(\d+)\s*(?:patients?|pts?|cases?)', combined_text, re.IGNORECASE)
                if patient_match:
                    patient_count = int(patient_match.group(1))
                    adverse_event_counts[ae_type]['patients'] += patient_count
                else:
                    # If no specific count found, assume at least 1 patient
                    adverse_event_counts[ae_type]['patients'] += 1
    
    # Create summary for dashboard
    ae_summary = []
    for ae_type, counts in sorted(adverse_event_counts.items(), key=lambda x: x[1]['papers'], reverse=True):
        if counts['papers'] > 0:
            ae_summary.append(f"{ae_type.title()}: {counts['papers']} papers, {counts['patients']} patients")
    
    dashboard_summary = "; ".join(ae_summary) if ae_summary else "Limited adverse event data available"
    
    print("\nAdverse Event Summary:")
    print(dashboard_summary)
    
    print(f"\nDetailed counts:")
    for ae_type, counts in sorted(adverse_event_counts.items(), key=lambda x: x[1]['papers'], reverse=True):
        if counts['papers'] > 0:
            print(f"  {ae_type}: {counts['papers']} papers, {counts['patients']} patients")
    
    # Save detailed analysis
    analysis_result = {
        'total_papers': len(data),
        'papers_with_ae_data': len(papers_with_ae),
        'papers_with_extractable_ae': len(all_ae_data),
        'adverse_event_counts': dict(adverse_event_counts),
        'dashboard_summary': dashboard_summary
    }
    
    with open('azacitidine_adverse_events_summary.json', 'w') as f:
        json.dump(analysis_result, f, indent=2)
    
    print(f"\nAnalysis saved to azacitidine_adverse_events_summary.json")
    
    return dashboard_summary, adverse_event_counts

if __name__ == "__main__":
    analyze_azacitidine_adverse_events()
