#!/usr/bin/env python3
"""
Analyze and count adverse events from decitabine CMML papers
"""

import json
import re

def analyze_decitabine_adverse_events():
    # Load the decitabine data
    with open('Decitabine_extracted.json', 'r') as f:
        data = json.load(f)
    
    print("Analyzing adverse events from decitabine papers...")
    
    # Collect all adverse events
    all_adverse_events = []
    
    for paper in data:
        pmid = paper['pmid']
        ae_data = paper.get('adverse_events', {})
        ae_text = ae_data.get('any_adverse_events', '')
        
        if ae_text:
            print(f"\nPMID {pmid}: {ae_text}")
            all_adverse_events.append({
                'pmid': pmid,
                'text': ae_text,
                'patients': paper.get('number_of_patients')
            })
    
    # Analyze and count adverse events
    adverse_event_counts = {}
    
    # Define common adverse events to look for
    ae_patterns = {
        'myelosuppression': r'myelosuppression|cytopenia|neutropenia|thrombocytopenia|anemia|leukopenia',
        'gastrointestinal': r'gastrointestinal|nausea|vomiting|diarrhea|abdominal|constipation',
        'fatigue': r'fatigue|tiredness|weakness|asthenia',
        'alopecia': r'alopecia|hair loss',
        'pneumonitis': r'pneumonitis|pulmonary|respiratory|interstitial|lung',
        'skin': r'skin|rash|dermatitis|pruritus',
        'hepatotoxicity': r'hepatotoxicity|liver|hepatic|elevated.*liver|transaminase',
        'renal': r'renal|kidney|nephrotoxicity|creatinine',
        'fever': r'fever|pyrexia',
        'infection': r'infection|sepsis|bacterial|fungal',
        'bleeding': r'bleeding|hemorrhage|petechiae|ecchymosis',
        'cardiac': r'cardiac|heart|arrhythmia|qt|prolonged',
        'neurological': r'neurological|neuropathy|dizziness|headache',
        'edema': r'edema|swelling|peripheral',
        'anorexia': r'anorexia|appetite|weight loss'
    }
    
    for paper in all_adverse_events:
        text = paper['text'].lower()
        patients = paper['patients'] or 1  # Default to 1 if not specified
        
        for ae_type, pattern in ae_patterns.items():
            if re.search(pattern, text):
                if ae_type not in adverse_event_counts:
                    adverse_event_counts[ae_type] = {
                        'count': 0,
                        'papers': [],
                        'total_patients': 0
                    }
                
                adverse_event_counts[ae_type]['count'] += 1
                adverse_event_counts[ae_type]['papers'].append(paper['pmid'])
                adverse_event_counts[ae_type]['total_patients'] += patients
    
    # Calculate percentages
    total_papers = len(all_adverse_events)
    total_patients = sum(p.get('patients', 1) for p in all_adverse_events)
    
    print(f"\n📊 Decitabine Adverse Events Analysis:")
    print(f"Total papers with AE data: {total_papers}")
    print(f"Total patients: {total_patients}")
    print(f"\nAdverse Event Counts:")
    
    for ae_type, data in adverse_event_counts.items():
        paper_percentage = (data['count'] / total_papers) * 100 if total_papers > 0 else 0
        patient_percentage = (data['total_patients'] / total_patients) * 100 if total_patients > 0 else 0
        
        print(f"  {ae_type.title()}: {data['count']} papers ({paper_percentage:.1f}%), {data['total_patients']} patients ({patient_percentage:.1f}%)")
        print(f"    Papers: {', '.join(data['papers'])}")
    
    # Create summary for dashboard
    ae_summary = []
    for ae_type, data in adverse_event_counts.items():
        if data['count'] > 0:
            if data['total_patients'] > 0:
                ae_summary.append(f"{ae_type.title()}: {data['count']} papers, {data['total_patients']} patients")
            else:
                ae_summary.append(f"{ae_type.title()}: {data['count']} papers")
    
    dashboard_summary = "; ".join(ae_summary) if ae_summary else "Limited adverse event data available"
    
    print(f"\n📋 Dashboard Summary:")
    print(dashboard_summary)
    
    return dashboard_summary, adverse_event_counts

if __name__ == "__main__":
    analyze_decitabine_adverse_events()
