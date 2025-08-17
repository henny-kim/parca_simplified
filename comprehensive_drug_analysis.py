#!/usr/bin/env python3
"""
Comprehensive Drug Analysis for CMML Treatments
Calculates median and mean values for efficacy, adverse events, and therapy duration
"""

import json
import numpy as np
import pandas as pd
from typing import List, Dict, Optional

class CMMLDrugAnalyzer:
    def __init__(self):
        self.results = {}
    
    def calculate_stats(self, values: List[float], metric_name: str) -> Dict:
        """Calculate median, mean, std, min, max for a list of values"""
        if not values:
            return {
                'count': 0,
                'median': None,
                'mean': None,
                'std': None,
                'min': None,
                'max': None,
                'values': []
            }
        
        values = [v for v in values if v is not None and not np.isnan(v)]
        if not values:
            return {'count': 0, 'median': None, 'mean': None, 'std': None, 'min': None, 'max': None, 'values': []}
            
        return {
            'count': len(values),
            'median': float(np.median(values)),
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'min': float(min(values)),
            'max': float(max(values)),
            'values': values
        }
    
    def analyze_azacitidine_efficacy(self):
        """Analyze azacitidine clinical efficacy data"""
        print("📊 Analyzing Azacitidine Clinical Efficacy...")
        
        with open('clinical_efficacy_azacitidine.json', 'r') as f:
            data = json.load(f)
        
        efficacy_papers = [p for p in data if p.get('has_efficacy_data')]
        
        metrics = {
            'complete_response': [p.get('complete_response') for p in efficacy_papers if p.get('complete_response') is not None],
            'overall_response_rate': [p.get('overall_response_rate') for p in efficacy_papers if p.get('overall_response_rate') is not None],
            'overall_survival_median': [p.get('overall_survival_median') for p in efficacy_papers if p.get('overall_survival_median') is not None],
            'progression_free_survival_median': [p.get('progression_free_survival_median') for p in efficacy_papers if p.get('progression_free_survival_median') is not None],
            'total_patients': [p.get('total_patients') for p in efficacy_papers if p.get('total_patients') is not None]
        }
        
        results = {}
        for metric, values in metrics.items():
            results[metric] = self.calculate_stats(values, metric)
            print(f"  {metric}: {results[metric]['count']} studies, median={results[metric]['median']}, mean={results[metric]['mean']:.1f}" if results[metric]['count'] > 0 else f"  {metric}: No data")
        
        self.results['azacitidine'] = {
            'efficacy': results,
            'total_papers': len(data),
            'papers_with_efficacy': len(efficacy_papers)
        }
        
        return results
    
    def analyze_adverse_events(self):
        """Analyze adverse events data"""
        print("\n⚠️  Analyzing Adverse Events...")
        
        try:
            with open('adverse_event_comprehensive.json', 'r') as f:
                ae_data = json.load(f)
            
            print(f"Adverse events data: {len(ae_data)} records")
            # Add detailed AE analysis here
            
        except FileNotFoundError:
            print("  Adverse events data not found - will need to extract")
            
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        
        report = {
            'analysis_date': '2024-08-16',
            'datasets_analyzed': list(self.results.keys()),
            'summary': {}
        }
        
        if 'azacitidine' in self.results:
            aza_efficacy = self.results['azacitidine']['efficacy']
            
            report['summary']['azacitidine'] = {
                'complete_response_rate': {
                    'median_percent': aza_efficacy['complete_response']['median'],
                    'mean_percent': aza_efficacy['complete_response']['mean'],
                    'studies': aza_efficacy['complete_response']['count']
                },
                'overall_response_rate': {
                    'median_percent': aza_efficacy['overall_response_rate']['median'], 
                    'mean_percent': aza_efficacy['overall_response_rate']['mean'],
                    'studies': aza_efficacy['overall_response_rate']['count']
                },
                'overall_survival': {
                    'median_months': aza_efficacy['overall_survival_median']['median'],
                    'mean_months': aza_efficacy['overall_survival_median']['mean'], 
                    'studies': aza_efficacy['overall_survival_median']['count']
                },
                'progression_free_survival': {
                    'median_months': aza_efficacy['progression_free_survival_median']['median'],
                    'mean_months': aza_efficacy['progression_free_survival_median']['mean'],
                    'studies': aza_efficacy['progression_free_survival_median']['count']
                }
            }
        
        # Save detailed results
        with open('comprehensive_drug_analysis_results.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

def main():
    print("🔬 COMPREHENSIVE CMML DRUG ANALYSIS")
    print("=" * 50)
    
    analyzer = CMMLDrugAnalyzer()
    
    # 1. Analyze Azacitidine (we have complete data)
    analyzer.analyze_azacitidine_efficacy()
    
    # 2. Analyze Adverse Events
    analyzer.analyze_adverse_events()
    
    # 3. Generate comprehensive report
    report = analyzer.generate_summary_report()
    
    print("\n📋 SUMMARY RESULTS:")
    print("=" * 30)
    
    if 'azacitidine' in report['summary']:
        aza = report['summary']['azacitidine']
        print(f"AZACITIDINE EFFICACY:")
        print(f"  Complete Response Rate: {aza['complete_response_rate']['median_percent']:.1f}% median, {aza['complete_response_rate']['mean_percent']:.1f}% mean ({aza['complete_response_rate']['studies']} studies)")
        print(f"  Overall Response Rate: {aza['overall_response_rate']['median_percent']:.1f}% median, {aza['overall_response_rate']['mean_percent']:.1f}% mean ({aza['overall_response_rate']['studies']} studies)")
        print(f"  Overall Survival: {aza['overall_survival']['median_months']:.1f} months median, {aza['overall_survival']['mean_months']:.1f} months mean ({aza['overall_survival']['studies']} studies)")
        if aza['progression_free_survival']['studies'] > 0:
            print(f"  Progression-Free Survival: {aza['progression_free_survival']['median_months']:.1f} months median, {aza['progression_free_survival']['mean_months']:.1f} months mean ({aza['progression_free_survival']['studies']} studies)")
    
    print(f"\n💾 Detailed results saved to: comprehensive_drug_analysis_results.json")
    
    print(f"\n🔄 Next Steps Needed:")
    print(f"  1. Extract decitabine clinical efficacy data")
    print(f"  2. Extract adverse events data for all drugs") 
    print(f"  3. Extract therapy duration/cycles data")
    print(f"  4. Create combined azacitidine + decitabine analysis")

if __name__ == "__main__":
    main()
