#!/usr/bin/env python3
"""
Update dashboard data with Azacitidine adverse events information
"""

import json
from collections import defaultdict

def analyze_azacitidine_adverse_events():
    """Analyze Azacitidine adverse events data and create summary for dashboard"""
    
    # Load comprehensive adverse events data
    with open('adverse_event_comprehensive.json', 'r') as f:
        comprehensive_data = json.load(f)
    
    azacitidine_papers = comprehensive_data.get('azacitidine', [])
    
    # Filter papers with adverse events data
    papers_with_ae = [p for p in azacitidine_papers if p.get('has_ae_data', False)]
    
    print(f"Found {len(papers_with_ae)} Azacitidine papers with adverse events data")
    
    # Analyze adverse events
    ae_summary = defaultdict(lambda: {'papers': 0, 'patients': 0})
    
    for paper in papers_with_ae:
        # Count hematologic adverse events
        hematologic_ae = paper.get('hematologic_ae', {})
        if hematologic_ae is not None:
            for ae_type, rate in hematologic_ae.items():
                if rate is not None:
                    ae_summary[ae_type]['papers'] += 1
                    ae_summary[ae_type]['patients'] += 1  # Simplified count
        
        # Count non-hematologic adverse events
        non_hematologic_ae = paper.get('non_hematologic_ae', {})
        if non_hematologic_ae is not None:
            for ae_type, rate in non_hematologic_ae.items():
                if rate is not None:
                    ae_summary[ae_type]['papers'] += 1
                    ae_summary[ae_type]['patients'] += 1  # Simplified count
    
    # Create summary string
    summary_parts = []
    for ae_type, counts in sorted(ae_summary.items(), key=lambda x: x[1]['papers'], reverse=True):
        if counts['papers'] > 0:
            summary_parts.append(f"{ae_type}: {counts['papers']} papers, {counts['patients']} patients")
    
    summary = "; ".join(summary_parts) if summary_parts else "Limited adverse event data available"
    
    return {
        'papers_with_ae': len(papers_with_ae),
        'total_papers': len(azacitidine_papers),
        'adverse_events_summary': summary,
        'ae_breakdown': dict(ae_summary)
    }

def update_dashboard_data():
    """Update the dashboard data with Azacitidine adverse events information"""
    
    # Load current dashboard data
    with open('updated_dashboard_data.json', 'r') as f:
        dashboard_data = json.load(f)
    
    # Analyze Azacitidine adverse events
    ae_analysis = analyze_azacitidine_adverse_events()
    
    # Update Azacitidine safety section
    if 'azacitidine' in dashboard_data:
        dashboard_data['azacitidine']['safety']['adverse_events_summary'] = ae_analysis['adverse_events_summary']
        
        # Add additional metadata
        if '_metadata' not in dashboard_data:
            dashboard_data['_metadata'] = {}
        if 'azacitidine_ae_analysis' not in dashboard_data['_metadata']:
            dashboard_data['_metadata']['azacitidine_ae_analysis'] = {}
        
        dashboard_data['_metadata']['azacitidine_ae_analysis'] = {
            'papers_with_ae': ae_analysis['papers_with_ae'],
            'total_papers': ae_analysis['total_papers'],
            'ae_breakdown': ae_analysis['ae_breakdown']
        }
    
    # Save updated dashboard data
    with open('updated_dashboard_data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    
    print("✅ Updated dashboard data with Azacitidine adverse events information")
    print(f"📊 Azacitidine papers with adverse events: {ae_analysis['papers_with_ae']}/{ae_analysis['total_papers']}")
    print(f"📋 Summary: {ae_analysis['adverse_events_summary'][:100]}...")

if __name__ == "__main__":
    update_dashboard_data()
