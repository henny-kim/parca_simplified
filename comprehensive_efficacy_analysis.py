#!/usr/bin/env python3
"""
Comprehensive Efficacy Analysis for CMML Treatments
Generates median and mean statistics for all requested metrics
"""

import json
import numpy as np
import pandas as pd
from statistics import median, mean
from typing import List, Dict, Optional

def safe_stats(values: List[float]) -> Dict:
    """Calculate statistics safely handling empty lists"""
    clean_values = [v for v in values if v is not None and not np.isnan(v)]
    if not clean_values:
        return {
            'count': 0, 'median': None, 'mean': None, 
            'std': None, 'min': None, 'max': None
        }
    
    return {
        'count': len(clean_values),
        'median': round(median(clean_values), 2),
        'mean': round(mean(clean_values), 2),
        'std': round(np.std(clean_values), 2),
        'min': round(min(clean_values), 2),
        'max': round(max(clean_values), 2),
        'values': clean_values
    }

def analyze_azacitidine():
    """Analyze azacitidine clinical efficacy data"""
    with open('clinical_efficacy_azacitidine.json', 'r') as f:
        data = json.load(f)
    
    efficacy_papers = [p for p in data if p.get('has_efficacy_data')]
    
    # Extract efficacy metrics
    cr_values = [p.get('complete_response') for p in efficacy_papers if p.get('complete_response') is not None]
    orr_values = [p.get('overall_response_rate') for p in efficacy_papers if p.get('overall_response_rate') is not None]
    os_values = [p.get('overall_survival_median') for p in efficacy_papers if p.get('overall_survival_median') is not None]
    pfs_values = [p.get('progression_free_survival_median') for p in efficacy_papers if p.get('progression_free_survival_median') is not None]
    
    return {
        'drug': 'Azacitidine',
        'total_papers': len(data),
        'efficacy_papers': len(efficacy_papers),
        'complete_response': safe_stats(cr_values),
        'overall_response_rate': safe_stats(orr_values),
        'overall_survival': safe_stats(os_values),
        'progression_free_survival': safe_stats(pfs_values)
    }

def analyze_adverse_events():
    """Analyze adverse events data"""
    try:
        with open('adverse_event_comprehensive.json', 'r') as f:
            ae_data = json.load(f)
        
        # Extract AE data by drug if available
        print(f"Found {len(ae_data)} adverse event records")
        # TODO: Implement AE analysis when data structure is clear
        
        return {'status': 'Limited data available', 'records': len(ae_data)}
    except FileNotFoundError:
        return {'status': 'Adverse events data not found'}

def generate_comprehensive_report():
    """Generate the complete report as requested"""
    
    print("🔬 COMPREHENSIVE CMML EFFICACY ANALYSIS")
    print("=" * 60)
    print()
    
    # 1. Azacitidine Analysis
    aza_results = analyze_azacitidine()
    
    print("📊 AZACITIDINE EFFICACY RESULTS:")
    print("-" * 40)
    print(f"Total papers analyzed: {aza_results['total_papers']}")
    print(f"Papers with efficacy data: {aza_results['efficacy_papers']}")
    print()
    
    print("COMPLETE RESPONSE (CR) RATES:")
    cr = aza_results['complete_response']
    if cr['count'] > 0:
        print(f"  • Median: {cr['median']}%")
        print(f"  • Mean: {cr['mean']}%")
        print(f"  • Studies: {cr['count']}")
        print(f"  • Range: {cr['min']}% - {cr['max']}%")
    else:
        print("  • No data available")
    print()
    
    print("OVERALL RESPONSE RATES (ORR):")
    orr = aza_results['overall_response_rate']
    if orr['count'] > 0:
        print(f"  • Median: {orr['median']}%")
        print(f"  • Mean: {orr['mean']}%")
        print(f"  • Studies: {orr['count']}")
        print(f"  • Range: {orr['min']}% - {orr['max']}%")
    else:
        print("  • No data available")
    print()
    
    print("OVERALL SURVIVAL (OS):")
    os = aza_results['overall_survival']
    if os['count'] > 0:
        print(f"  • Median: {os['median']} months")
        print(f"  • Mean: {os['mean']} months")
        print(f"  • Studies: {os['count']}")
        print(f"  • Range: {os['min']} - {os['max']} months")
    else:
        print("  • No data available")
    print()
    
    print("PROGRESSION-FREE SURVIVAL (PFS):")
    pfs = aza_results['progression_free_survival']
    if pfs['count'] > 0:
        print(f"  • Median: {pfs['median']} months")
        print(f"  • Mean: {pfs['mean']} months")
        print(f"  • Studies: {pfs['count']}")
        print(f"  • Range: {pfs['min']} - {pfs['max']} months")
    else:
        print("  • No data available")
    print()
    
    # 2. Adverse Events Analysis
    print("⚠️  ADVERSE EVENTS ANALYSIS:")
    print("-" * 40)
    ae_results = analyze_adverse_events()
    print(f"Status: {ae_results.get('status', 'Unknown')}")
    if 'records' in ae_results:
        print(f"Records found: {ae_results['records']}")
    print()
    
    # 3. Summary for requested analysis
    print("📋 SUMMARY FOR REQUESTED METRICS:")
    print("-" * 40)
    print("COMPLETED:")
    print("✅ Azacitidine CR rates (median & mean)")
    print("✅ Azacitidine ORR (median & mean)")
    print("✅ Azacitidine OS (median & mean)")
    print("✅ Azacitidine PFS (median & mean)")
    print()
    print("STILL NEEDED:")
    print("🔄 Decitabine clinical efficacy extraction")
    print("🔄 Third product identification and analysis")
    print("🔄 Adverse events by individual product")
    print("🔄 Therapy duration/cycles analysis")
    print("🔄 Combined azacitidine + decitabine analysis")
    print()
    
    # Save results
    final_results = {
        'analysis_date': '2024-08-16',
        'azacitidine': aza_results,
        'adverse_events': ae_results,
        'status': {
            'azacitidine_complete': True,
            'decitabine_needed': True,
            'adverse_events_needed': True,
            'therapy_duration_needed': True
        }
    }
    
    with open('comprehensive_efficacy_results.json', 'w') as f:
        json.dump(final_results, f, indent=2)
    
    print(f"💾 Detailed results saved to: comprehensive_efficacy_results.json")
    
    return final_results

if __name__ == "__main__":
    results = generate_comprehensive_report()
