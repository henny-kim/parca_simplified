#!/usr/bin/env python3
"""
Analyze Decitabine Clinical Efficacy Data and Update Dashboard
"""

import json
import statistics
from typing import Dict, List, Any
import pandas as pd

def load_decitabine_data():
    """Load the decitabine extraction results."""
    with open('Decitabine_extracted.json', 'r') as f:
        return json.load(f)

def analyze_decitabine_efficacy(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze decitabine efficacy data and generate summary statistics."""
    
    # Filter papers with efficacy data
    efficacy_papers = [paper for paper in data if paper.get('has_efficacy_data')]
    
    # Extract response rates
    complete_responses = []
    overall_response_rates = []
    progression_free_survivals = []
    overall_survivals = []
    total_patients_list = []
    cmml_patients_list = []
    
    # Collect supporting quotes
    all_quotes = []
    
    for paper in efficacy_papers:
        # Complete response
        cr = paper.get('complete_response')
        if cr is not None and isinstance(cr, (int, float)):
            complete_responses.append(cr)
        
        # Overall response rate
        orr = paper.get('overall_response_rate')
        if orr is not None:
            if isinstance(orr, dict):
                # Handle comparative studies
                for arm, rate in orr.items():
                    if isinstance(rate, (int, float)):
                        overall_response_rates.append(rate)
            elif isinstance(orr, (int, float)):
                overall_response_rates.append(orr)
        
        # Progression-free survival
        pfs = paper.get('progression_free_survival_median')
        if pfs is not None:
            if isinstance(pfs, dict):
                for arm, survival in pfs.items():
                    if isinstance(survival, (int, float)):
                        progression_free_survivals.append(survival)
            elif isinstance(pfs, (int, float)):
                progression_free_survivals.append(pfs)
        
        # Overall survival
        os = paper.get('overall_survival_median')
        if os is not None:
            if isinstance(os, dict):
                for arm, survival in os.items():
                    if isinstance(survival, (int, float)):
                        overall_survivals.append(survival)
            elif isinstance(os, (int, float)):
                overall_survivals.append(os)
        
        # Patient numbers
        total = paper.get('total_patients')
        if total is not None and isinstance(total, int):
            total_patients_list.append(total)
        
        cmml = paper.get('cmml_patients')
        if cmml is not None and isinstance(cmml, int):
            cmml_patients_list.append(cmml)
        
        # Supporting quotes
        quotes = paper.get('supporting_quotes', [])
        all_quotes.extend(quotes)
    
    # Calculate statistics
    analysis = {
        'total_papers': len(data),
        'papers_with_efficacy': len(efficacy_papers),
        'efficacy_rate': len(efficacy_papers) / len(data) * 100 if data else 0,
        
        'complete_response': {
            'count': len(complete_responses),
            'mean': statistics.mean(complete_responses) if complete_responses else None,
            'median': statistics.median(complete_responses) if complete_responses else None,
            'min': min(complete_responses) if complete_responses else None,
            'max': max(complete_responses) if complete_responses else None,
            'values': complete_responses
        },
        
        'overall_response_rate': {
            'count': len(overall_response_rates),
            'mean': statistics.mean(overall_response_rates) if overall_response_rates else None,
            'median': statistics.median(overall_response_rates) if overall_response_rates else None,
            'min': min(overall_response_rates) if overall_response_rates else None,
            'max': max(overall_response_rates) if overall_response_rates else None,
            'values': overall_response_rates
        },
        
        'progression_free_survival': {
            'count': len(progression_free_survivals),
            'mean': statistics.mean(progression_free_survivals) if progression_free_survivals else None,
            'median': statistics.median(progression_free_survivals) if progression_free_survivals else None,
            'min': min(progression_free_survivals) if progression_free_survivals else None,
            'max': max(progression_free_survivals) if progression_free_survivals else None,
            'values': progression_free_survivals
        },
        
        'overall_survival': {
            'count': len(overall_survivals),
            'mean': statistics.mean(overall_survivals) if overall_survivals else None,
            'median': statistics.median(overall_survivals) if overall_survivals else None,
            'min': min(overall_survivals) if overall_survivals else None,
            'max': max(overall_survivals) if overall_survivals else None,
            'values': overall_survivals
        },
        
        'patient_numbers': {
            'total_patients': {
                'count': len(total_patients_list),
                'sum': sum(total_patients_list) if total_patients_list else 0,
                'mean': statistics.mean(total_patients_list) if total_patients_list else None,
                'median': statistics.median(total_patients_list) if total_patients_list else None
            },
            'cmml_patients': {
                'count': len(cmml_patients_list),
                'sum': sum(cmml_patients_list) if cmml_patients_list else 0,
                'mean': statistics.mean(cmml_patients_list) if cmml_patients_list else None,
                'median': statistics.median(cmml_patients_list) if cmml_patients_list else None
            }
        },
        
        'supporting_quotes_count': len(all_quotes),
        'key_findings': []
    }
    
    # Extract key findings from efficacy papers
    for paper in efficacy_papers[:10]:  # Top 10 papers
        if paper.get('efficacy_summary'):
            analysis['key_findings'].append({
                'pmid': paper.get('pmid'),
                'citation': paper.get('citation'),
                'summary': paper.get('efficacy_summary'),
                'orr': paper.get('overall_response_rate'),
                'os': paper.get('overall_survival_median'),
                'pfs': paper.get('progression_free_survival_median')
            })
    
    return analysis

def create_dashboard_data(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Create dashboard-compatible data structure."""
    
    dashboard_data = {
        'drug': 'decitabine',
        'extraction_summary': {
            'total_papers_analyzed': analysis['total_papers'],
            'papers_with_efficacy_data': analysis['papers_with_efficacy'],
            'efficacy_data_rate': round(analysis['efficacy_rate'], 1),
            'total_cmml_patients': analysis['patient_numbers']['cmml_patients']['sum'],
            'total_study_patients': analysis['patient_numbers']['total_patients']['sum']
        },
        
        'efficacy_metrics': {
            'overall_response_rate': {
                'median': round(analysis['overall_response_rate']['median'], 1) if analysis['overall_response_rate']['median'] else None,
                'range': f"{analysis['overall_response_rate']['min']}-{analysis['overall_response_rate']['max']}" if analysis['overall_response_rate']['min'] and analysis['overall_response_rate']['max'] else None,
                'studies_count': analysis['overall_response_rate']['count']
            },
            'complete_response_rate': {
                'median': round(analysis['complete_response']['median'], 1) if analysis['complete_response']['median'] else None,
                'range': f"{analysis['complete_response']['min']}-{analysis['complete_response']['max']}" if analysis['complete_response']['min'] and analysis['complete_response']['max'] else None,
                'studies_count': analysis['complete_response']['count']
            },
            'overall_survival': {
                'median': round(analysis['overall_survival']['median'], 1) if analysis['overall_survival']['median'] else None,
                'range': f"{analysis['overall_survival']['min']}-{analysis['overall_survival']['max']}" if analysis['overall_survival']['min'] and analysis['overall_survival']['max'] else None,
                'studies_count': analysis['overall_survival']['count']
            },
            'progression_free_survival': {
                'median': round(analysis['progression_free_survival']['median'], 1) if analysis['progression_free_survival']['median'] else None,
                'range': f"{analysis['progression_free_survival']['min']}-{analysis['progression_free_survival']['max']}" if analysis['progression_free_survival']['min'] and analysis['progression_free_survival']['max'] else None,
                'studies_count': analysis['progression_free_survival']['count']
            }
        },
        
        'key_studies': analysis['key_findings'][:5],  # Top 5 studies
        
        'comparison_with_azacitidine': {
            'note': 'Comparison data will be added when azacitidine analysis is available'
        }
    }
    
    return dashboard_data

def main():
    """Main analysis function."""
    print("Loading decitabine data...")
    data = load_decitabine_data()
    
    print("Analyzing efficacy data...")
    analysis = analyze_decitabine_efficacy(data)
    
    print("Creating dashboard data...")
    dashboard_data = create_dashboard_data(analysis)
    
    # Save analysis results
    with open('decitabine_analysis_results.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    with open('decitabine_dashboard_data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("DECITABINE ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total papers analyzed: {analysis['total_papers']}")
    print(f"Papers with efficacy data: {analysis['papers_with_efficacy']} ({analysis['efficacy_rate']:.1f}%)")
    print(f"Total CMML patients: {analysis['patient_numbers']['cmml_patients']['sum']}")
    print(f"Total study patients: {analysis['patient_numbers']['total_patients']['sum']}")
    
    print(f"\nOverall Response Rate:")
    print(f"  Median: {analysis['overall_response_rate']['median']:.1f}% (n={analysis['overall_response_rate']['count']})")
    print(f"  Range: {analysis['overall_response_rate']['min']:.1f}-{analysis['overall_response_rate']['max']:.1f}%")
    
    print(f"\nComplete Response Rate:")
    print(f"  Median: {analysis['complete_response']['median']:.1f}% (n={analysis['complete_response']['count']})")
    print(f"  Range: {analysis['complete_response']['min']:.1f}-{analysis['complete_response']['max']:.1f}%")
    
    print(f"\nOverall Survival:")
    print(f"  Median: {analysis['overall_survival']['median']:.1f} months (n={analysis['overall_survival']['count']})")
    print(f"  Range: {analysis['overall_survival']['min']:.1f}-{analysis['overall_survival']['max']:.1f} months")
    
    print(f"\nProgression-Free Survival:")
    print(f"  Median: {analysis['progression_free_survival']['median']:.1f} months (n={analysis['progression_free_survival']['count']})")
    print(f"  Range: {analysis['progression_free_survival']['min']:.1f}-{analysis['progression_free_survival']['max']:.1f} months")
    
    print(f"\nFiles saved:")
    print(f"  - decitabine_analysis_results.json")
    print(f"  - decitabine_dashboard_data.json")

if __name__ == "__main__":
    main()
