#!/usr/bin/env python3
"""
Comprehensive Dashboard Analysis Update
Calculates accurate statistics from clinical efficacy data and updates dashboard
"""

import json
import numpy as np
from datetime import datetime

def load_azacitidine_data():
    """Load and parse azacitidine clinical efficacy data"""
    try:
        with open('clinical_efficacy_azacitidine.json', 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("❌ clinical_efficacy_azacitidine.json not found")
        return []

def calculate_statistics(data):
    """Calculate comprehensive statistics from clinical efficacy data"""
    
    # Filter papers with efficacy data
    efficacy_papers = [paper for paper in data if paper.get('has_efficacy_data', False)]
    
    # Extract numeric values for each metric
    complete_response_rates = []
    overall_response_rates = []
    overall_survival_data = []
    progression_free_survival_data = []
    total_patients_data = []
    
    for paper in efficacy_papers:
        # Complete Response Rate
        if paper.get('complete_response') is not None:
            complete_response_rates.append(float(paper['complete_response']))
        
        # Overall Response Rate
        if paper.get('overall_response_rate') is not None:
            overall_response_rates.append(float(paper['overall_response_rate']))
        
        # Overall Survival (months)
        if paper.get('overall_survival_median') is not None:
            overall_survival_data.append(float(paper['overall_survival_median']))
        
        # Progression Free Survival (months)
        if paper.get('progression_free_survival_median') is not None:
            progression_free_survival_data.append(float(paper['progression_free_survival_median']))
        
        # Total Patients
        if paper.get('total_patients') is not None:
            total_patients_data.append(int(paper['total_patients']))
    
    # Calculate statistics
    stats = {
        'complete_response': {
            'mean': round(np.mean(complete_response_rates), 1) if complete_response_rates else None,
            'median': round(np.median(complete_response_rates), 1) if complete_response_rates else None,
            'studies': len(complete_response_rates),
            'range': f"{min(complete_response_rates):.1f}-{max(complete_response_rates):.1f}%" if complete_response_rates else None
        },
        'overall_response_rate': {
            'mean': round(np.mean(overall_response_rates), 1) if overall_response_rates else None,
            'median': round(np.median(overall_response_rates), 1) if overall_response_rates else None,
            'studies': len(overall_response_rates),
            'range': f"{min(overall_response_rates):.1f}-{max(overall_response_rates):.1f}%" if overall_response_rates else None
        },
        'overall_survival': {
            'mean': round(np.mean(overall_survival_data), 1) if overall_survival_data else None,
            'median': round(np.median(overall_survival_data), 1) if overall_survival_data else None,
            'studies': len(overall_survival_data),
            'range': f"{min(overall_survival_data):.1f}-{max(overall_survival_data):.1f} months" if overall_survival_data else None
        },
        'progression_free_survival': {
            'mean': round(np.mean(progression_free_survival_data), 1) if progression_free_survival_data else None,
            'median': round(np.median(progression_free_survival_data), 1) if progression_free_survival_data else None,
            'studies': len(progression_free_survival_data),
            'range': f"{min(progression_free_survival_data):.1f}-{max(progression_free_survival_data):.1f} months" if progression_free_survival_data else None
        },
        'total_patients': {
            'mean': round(np.mean(total_patients_data), 0) if total_patients_data else None,
            'median': round(np.median(total_patients_data), 0) if total_patients_data else None,
            'studies': len(total_patients_data),
            'range': f"{min(total_patients_data)}-{max(total_patients_data)} patients" if total_patients_data else None
        }
    }
    
    return stats, len(efficacy_papers), len(data)

def create_dashboard_summary(azacitidine_stats, efficacy_papers_count, total_papers):
    """Create comprehensive dashboard summary"""
    
    summary = {
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'paper_counts': {
            'azacitidine_total': total_papers,
            'azacitidine_with_efficacy': efficacy_papers_count,
            'decitabine_total': 125,  # From pubmed data
            'decitabine_with_efficacy': 'Pending extraction',
            'hydroxyurea_total': 9,   # From pubmed data
            'hydroxyurea_with_efficacy': 'Pending extraction',
            'total_unique_papers': total_papers + 125 + 9
        },
        'azacitidine_metrics': {
            'efficacy': {
                'complete_response': {
                    'mean': azacitidine_stats['complete_response']['mean'],
                    'median': azacitidine_stats['complete_response']['median'],
                    'studies': azacitidine_stats['complete_response']['studies'],
                    'range': azacitidine_stats['complete_response']['range']
                },
                'overall_response_rate': {
                    'mean': azacitidine_stats['overall_response_rate']['mean'],
                    'median': azacitidine_stats['overall_response_rate']['median'],
                    'studies': azacitidine_stats['overall_response_rate']['studies'],
                    'range': azacitidine_stats['overall_response_rate']['range']
                }
            },
            'survival': {
                'progression_free_survival': {
                    'mean': azacitidine_stats['progression_free_survival']['mean'],
                    'median': azacitidine_stats['progression_free_survival']['median'],
                    'studies': azacitidine_stats['progression_free_survival']['studies'],
                    'range': azacitidine_stats['progression_free_survival']['range']
                },
                'overall_survival': {
                    'mean': azacitidine_stats['overall_survival']['mean'],
                    'median': azacitidine_stats['overall_survival']['median'],
                    'studies': azacitidine_stats['overall_survival']['studies'],
                    'range': azacitidine_stats['overall_survival']['range']
                }
            },
            'safety': {
                'serious_adverse_events': {
                    'mean': None,
                    'median': None,
                    'studies': 0,
                    'range': None,
                    'note': 'Available in adverse_events_comprehensive.json'
                },
                'comprehensive_adverse_events': {
                    'status': 'LLM-extracted data available',
                    'file': 'adverse_events_comprehensive.json'
                }
            },
            'therapy_duration': {
                'duration_cycles': {
                    'mean': None,
                    'median': None,
                    'studies': 0,
                    'range': None,
                    'note': 'Data extraction needed'
                }
            }
        },
        'decitabine_metrics': {
            'status': 'Extraction in progress',
            'papers_available': 125,
            'estimated_completion': '4-6 hours'
        },
        'hydroxyurea_metrics': {
            'status': 'Pending extraction',
            'papers_available': 9
        },
        'combined_analysis': {
            'status': 'Pending decitabine completion',
            'total_papers_when_complete': total_papers + 125 + 9
        },
        'data_quality': {
            'extraction_method': 'LLM-based using Gemini 1.5 Flash',
            'confidence_scores': 'Included in individual records',
            'supporting_quotes': 'Extracted for all positive findings',
            'structured_format': 'JSON with standardized fields'
        }
    }
    
    return summary

def save_summary(summary, filename='dashboard_analysis_summary.json'):
    """Save summary to JSON file"""
    with open(filename, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Summary saved to: {filename}")

def print_summary(summary):
    """Print formatted summary to console"""
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE DASHBOARD ANALYSIS SUMMARY")
    print("="*80)
    
    print(f"\n📅 Analysis Date: {summary['analysis_date']}")
    
    print(f"\n📋 PAPER COUNTS:")
    print(f"   • Azacitidine: {summary['paper_counts']['azacitidine_with_efficacy']}/{summary['paper_counts']['azacitidine_total']} papers with efficacy data")
    print(f"   • Decitabine: {summary['paper_counts']['decitabine_with_efficacy']} ({summary['paper_counts']['decitabine_total']} total)")
    print(f"   • Hydroxyurea: {summary['paper_counts']['hydroxyurea_with_efficacy']} ({summary['paper_counts']['hydroxyurea_total']} total)")
    print(f"   • Total Unique Papers: {summary['paper_counts']['total_unique_papers']}")
    
    print(f"\n💊 AZACITIDINE METRICS:")
    az_metrics = summary['azacitidine_metrics']
    
    print(f"   📈 EFFICACY:")
    cr = az_metrics['efficacy']['complete_response']
    orr = az_metrics['efficacy']['overall_response_rate']
    print(f"      • Complete Response (CR): {cr['mean']}% (mean) / {cr['median']}% (median) [{cr['studies']} studies]")
    print(f"      • Overall Response Rate (ORR): {orr['mean']}% (mean) / {orr['median']}% (median) [{orr['studies']} studies]")
    
    print(f"   🕐 SURVIVAL:")
    pfs = az_metrics['survival']['progression_free_survival']
    os = az_metrics['survival']['overall_survival']
    print(f"      • Progression-Free Survival (PFS): {pfs['mean']} months (mean) / {pfs['median']} months (median) [{pfs['studies']} studies]")
    print(f"      • Overall Survival (OS): {os['mean']} months (mean) / {os['median']} months (median) [{os['studies']} studies]")
    
    print(f"   ⚠️  SAFETY:")
    print(f"      • Serious Adverse Events: {az_metrics['safety']['serious_adverse_events']['note']}")
    print(f"      • Comprehensive Adverse Events: {az_metrics['safety']['comprehensive_adverse_events']['status']}")
    
    print(f"   ⏱️  THERAPY DURATION:")
    print(f"      • Duration of Therapy (Cycles): {az_metrics['therapy_duration']['duration_cycles']['note']}")
    
    print(f"\n🔄 DECITABINE STATUS:")
    print(f"   • {summary['decitabine_metrics']['status']}")
    print(f"   • Papers available: {summary['decitabine_metrics']['papers_available']}")
    print(f"   • Estimated completion: {summary['decitabine_metrics']['estimated_completion']}")
    
    print(f"\n📊 DATA QUALITY:")
    print(f"   • Extraction method: {summary['data_quality']['extraction_method']}")
    print(f"   • Confidence scores: {summary['data_quality']['confidence_scores']}")
    print(f"   • Supporting quotes: {summary['data_quality']['supporting_quotes']}")
    
    print("\n" + "="*80)

def main():
    """Main analysis function"""
    print("🔍 Loading azacitidine clinical efficacy data...")
    
    # Load data
    azacitidine_data = load_azacitidine_data()
    if not azacitidine_data:
        print("❌ No azacitidine data found. Exiting.")
        return
    
    print(f"✅ Loaded {len(azacitidine_data)} azacitidine papers")
    
    # Calculate statistics
    print("📊 Calculating comprehensive statistics...")
    stats, efficacy_count, total_count = calculate_statistics(azacitidine_data)
    
    # Create summary
    print("📋 Creating dashboard summary...")
    summary = create_dashboard_summary(stats, efficacy_count, total_count)
    
    # Save and display
    save_summary(summary)
    print_summary(summary)
    
    print("\n🎯 NEXT STEPS:")
    print("   1. Complete decitabine clinical efficacy extraction")
    print("   2. Extract hydroxyurea clinical efficacy data")
    print("   3. Analyze adverse events by individual drug")
    print("   4. Calculate therapy duration/cycles data")
    print("   5. Generate combined azacitidine + decitabine analysis")

if __name__ == "__main__":
    main()
