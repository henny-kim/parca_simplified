#!/usr/bin/env python3
"""
Comprehensive Adverse Events Analysis
Calculate median and mean adverse events by individual drug
"""

import json
import numpy as np
from datetime import datetime

def load_adverse_events_data():
    """Load comprehensive adverse events data"""
    try:
        with open('adverse_event_comprehensive.json', 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("❌ adverse_event_comprehensive.json not found")
        return {}

def calculate_ae_statistics(data):
    """Calculate comprehensive AE statistics by drug"""
    
    results = {}
    
    for drug, papers in data.items():
        print(f"📊 Analyzing {drug} adverse events data...")
        
        # Filter papers with AE data
        ae_papers = [paper for paper in papers if paper.get('has_ae_data', False)]
        
        # Extract numeric values for each metric
        any_grade_ae_rates = []
        grade_3_4_ae_rates = []
        serious_ae_rates = []
        treatment_related_ae_rates = []
        discontinuation_rates = []
        dose_reduction_rates = []
        
        for paper in ae_papers:
            # Any grade AE rate
            if paper.get('any_grade_ae_rate') is not None:
                any_grade_ae_rates.append(float(paper['any_grade_ae_rate']))
            
            # Grade 3-4 AE rate
            if paper.get('grade_3_4_ae_rate') is not None:
                grade_3_4_ae_rates.append(float(paper['grade_3_4_ae_rate']))
            
            # Serious AE rate
            if paper.get('serious_ae_rate') is not None:
                serious_ae_rates.append(float(paper['serious_ae_rate']))
            
            # Treatment-related AE rate
            if paper.get('treatment_related_ae_rate') is not None:
                treatment_related_ae_rates.append(float(paper['treatment_related_ae_rate']))
            
            # Discontinuation rate
            if paper.get('discontinuation_rate') is not None:
                discontinuation_rates.append(float(paper['discontinuation_rate']))
            
            # Dose reduction rate
            if paper.get('dose_reduction_rate') is not None:
                dose_reduction_rates.append(float(paper['dose_reduction_rate']))
        
        # Calculate statistics
        drug_stats = {
            'total_papers': len(papers),
            'papers_with_ae_data': len(ae_papers),
            'any_grade_ae': {
                'mean': round(np.mean(any_grade_ae_rates), 1) if any_grade_ae_rates else None,
                'median': round(np.median(any_grade_ae_rates), 1) if any_grade_ae_rates else None,
                'studies': len(any_grade_ae_rates),
                'range': f"{min(any_grade_ae_rates):.1f}-{max(any_grade_ae_rates):.1f}%" if any_grade_ae_rates else None
            },
            'grade_3_4_ae': {
                'mean': round(np.mean(grade_3_4_ae_rates), 1) if grade_3_4_ae_rates else None,
                'median': round(np.median(grade_3_4_ae_rates), 1) if grade_3_4_ae_rates else None,
                'studies': len(grade_3_4_ae_rates),
                'range': f"{min(grade_3_4_ae_rates):.1f}-{max(grade_3_4_ae_rates):.1f}%" if grade_3_4_ae_rates else None
            },
            'serious_ae': {
                'mean': round(np.mean(serious_ae_rates), 1) if serious_ae_rates else None,
                'median': round(np.median(serious_ae_rates), 1) if serious_ae_rates else None,
                'studies': len(serious_ae_rates),
                'range': f"{min(serious_ae_rates):.1f}-{max(serious_ae_rates):.1f}%" if serious_ae_rates else None
            },
            'treatment_related_ae': {
                'mean': round(np.mean(treatment_related_ae_rates), 1) if treatment_related_ae_rates else None,
                'median': round(np.median(treatment_related_ae_rates), 1) if treatment_related_ae_rates else None,
                'studies': len(treatment_related_ae_rates),
                'range': f"{min(treatment_related_ae_rates):.1f}-{max(treatment_related_ae_rates):.1f}%" if treatment_related_ae_rates else None
            },
            'discontinuation_rate': {
                'mean': round(np.mean(discontinuation_rates), 1) if discontinuation_rates else None,
                'median': round(np.median(discontinuation_rates), 1) if discontinuation_rates else None,
                'studies': len(discontinuation_rates),
                'range': f"{min(discontinuation_rates):.1f}-{max(discontinuation_rates):.1f}%" if discontinuation_rates else None
            },
            'dose_reduction_rate': {
                'mean': round(np.mean(dose_reduction_rates), 1) if dose_reduction_rates else None,
                'median': round(np.median(dose_reduction_rates), 1) if dose_reduction_rates else None,
                'studies': len(dose_reduction_rates),
                'range': f"{min(dose_reduction_rates):.1f}-{max(dose_reduction_rates):.1f}%" if dose_reduction_rates else None
            }
        }
        
        results[drug] = drug_stats
        
        print(f"   ✅ {drug}: {len(ae_papers)} papers with AE data")
    
    return results

def create_combined_analysis(ae_stats, clinical_stats):
    """Create combined azacitidine + decitabine analysis"""
    
    # For now, we only have azacitidine clinical data
    # This will be expanded when decitabine extraction is complete
    
    combined_stats = {
        'azacitidine': {
            'clinical_efficacy': clinical_stats.get('azacitidine', {}),
            'adverse_events': ae_stats.get('azacitidine', {})
        },
        'decitabine': {
            'clinical_efficacy': {'status': 'Extraction in progress'},
            'adverse_events': ae_stats.get('decitabine', {})
        },
        'combined_analysis': {
            'status': 'Pending decitabine clinical efficacy completion',
            'estimated_completion': '4-6 hours'
        }
    }
    
    return combined_stats

def save_analysis(ae_stats, combined_stats, filename='comprehensive_ae_analysis.json'):
    """Save analysis results"""
    analysis = {
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'adverse_events_by_drug': ae_stats,
        'combined_analysis': combined_stats
    }
    
    with open(filename, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"✅ Analysis saved to: {filename}")

def print_analysis_summary(ae_stats):
    """Print formatted analysis summary"""
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE ADVERSE EVENTS ANALYSIS")
    print("="*80)
    
    for drug, stats in ae_stats.items():
        print(f"\n💊 {drug.upper()}:")
        print(f"   📋 Papers: {stats['papers_with_ae_data']}/{stats['total_papers']} with AE data")
        
        print(f"   ⚠️  ANY GRADE ADVERSE EVENTS:")
        ae = stats['any_grade_ae']
        if ae['studies'] > 0:
            print(f"      • Mean: {ae['mean']}% | Median: {ae['median']}% [{ae['studies']} studies]")
            print(f"      • Range: {ae['range']}")
        else:
            print(f"      • No data available")
        
        print(f"   🔴 GRADE 3-4 ADVERSE EVENTS:")
        grade34 = stats['grade_3_4_ae']
        if grade34['studies'] > 0:
            print(f"      • Mean: {grade34['mean']}% | Median: {grade34['median']}% [{grade34['studies']} studies]")
            print(f"      • Range: {grade34['range']}")
        else:
            print(f"      • No data available")
        
        print(f"   🚨 SERIOUS ADVERSE EVENTS:")
        sae = stats['serious_ae']
        if sae['studies'] > 0:
            print(f"      • Mean: {sae['mean']}% | Median: {sae['median']}% [{sae['studies']} studies]")
            print(f"      • Range: {sae['range']}")
        else:
            print(f"      • No data available")
        
        print(f"   💊 TREATMENT-RELATED ADVERSE EVENTS:")
        trae = stats['treatment_related_ae']
        if trae['studies'] > 0:
            print(f"      • Mean: {trae['mean']}% | Median: {trae['median']}% [{trae['studies']} studies]")
            print(f"      • Range: {trae['range']}")
        else:
            print(f"      • No data available")
        
        print(f"   ⏹️  DISCONTINUATION RATE:")
        disc = stats['discontinuation_rate']
        if disc['studies'] > 0:
            print(f"      • Mean: {disc['mean']}% | Median: {disc['median']}% [{disc['studies']} studies]")
            print(f"      • Range: {disc['range']}")
        else:
            print(f"      • No data available")
        
        print(f"   📉 DOSE REDUCTION RATE:")
        dose_red = stats['dose_reduction_rate']
        if dose_red['studies'] > 0:
            print(f"      • Mean: {dose_red['mean']}% | Median: {dose_red['median']}% [{dose_red['studies']} studies]")
            print(f"      • Range: {dose_red['range']}")
        else:
            print(f"      • No data available")
    
    print("\n" + "="*80)

def main():
    """Main analysis function"""
    print("🔍 Loading adverse events data...")
    
    # Load adverse events data
    ae_data = load_adverse_events_data()
    if not ae_data:
        print("❌ No adverse events data found. Exiting.")
        return
    
    print(f"✅ Loaded adverse events data for {len(ae_data)} drugs")
    
    # Calculate AE statistics
    print("📊 Calculating adverse events statistics...")
    ae_stats = calculate_ae_statistics(ae_data)
    
    # Load clinical efficacy data for combined analysis
    clinical_stats = {}
    try:
        with open('clinical_efficacy_azacitidine.json', 'r') as f:
            azacitidine_data = json.load(f)
        
        # Calculate basic clinical stats
        efficacy_papers = [p for p in azacitidine_data if p.get('has_efficacy_data', False)]
        clinical_stats['azacitidine'] = {
            'total_papers': len(azacitidine_data),
            'papers_with_efficacy': len(efficacy_papers),
            'status': 'Complete'
        }
    except FileNotFoundError:
        print("⚠️  Clinical efficacy data not found - will create basic combined analysis")
    
    # Create combined analysis
    print("🔗 Creating combined analysis...")
    combined_stats = create_combined_analysis(ae_stats, clinical_stats)
    
    # Save and display results
    save_analysis(ae_stats, combined_stats)
    print_analysis_summary(ae_stats)
    
    print("\n🎯 NEXT STEPS:")
    print("   1. Run enhanced clinical efficacy extraction for better PFS/therapy duration data")
    print("   2. Complete decitabine clinical efficacy extraction")
    print("   3. Extract hydroxyurea clinical efficacy data")
    print("   4. Generate final combined azacitidine + decitabine analysis")

if __name__ == "__main__":
    main()
