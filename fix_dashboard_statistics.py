#!/usr/bin/env python3
"""
Fix dashboard statistics by recalculating means/medians and deduplicating papers
"""

import json
import statistics
from collections import defaultdict

def extract_numeric_value(value):
    """Extract numeric value from various data formats"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace('%', ''))
        except:
            return None
    if isinstance(value, dict):
        # Handle cases like {'DEC-C': 64.0, 'DEC-C-Ven': 90.0}
        values = [v for v in value.values() if isinstance(v, (int, float))]
        return statistics.mean(values) if values else None
    return None

def calculate_statistics(values):
    """Calculate mean and median from a list of values"""
    if not values:
        return None, None
    
    valid_values = [v for v in values if v is not None and not (isinstance(v, str) and v.lower() in ['na', 'n/a', ''])]
    
    if not valid_values:
        return None, None
    
    try:
        mean_val = statistics.mean(valid_values)
        median_val = statistics.median(valid_values)
        return round(mean_val, 1), round(median_val, 1)
    except:
        return None, None

def analyze_azacitidine_data():
    """Analyze Azacitidine clinical efficacy data"""
    with open('clinical_efficacy_azacitidine.json', 'r') as f:
        data = json.load(f)
    
    papers_with_data = [p for p in data if p.get('has_efficacy_data')]
    
    # Extract values
    cr_values = [extract_numeric_value(p.get('complete_response')) for p in papers_with_data]
    orr_values = [extract_numeric_value(p.get('overall_response_rate')) for p in papers_with_data]
    pfs_values = [extract_numeric_value(p.get('progression_free_survival_median')) for p in papers_with_data]
    os_values = [extract_numeric_value(p.get('overall_survival_median')) for p in papers_with_data]
    
    # Calculate statistics
    cr_mean, cr_median = calculate_statistics(cr_values)
    orr_mean, orr_median = calculate_statistics(orr_values)
    pfs_mean, pfs_median = calculate_statistics(pfs_values)
    os_mean, os_median = calculate_statistics(os_values)
    
    print(f"Azacitidine Analysis:")
    print(f"  Papers with efficacy data: {len(papers_with_data)}")
    print(f"  CR - Mean: {cr_mean}, Median: {cr_median} (from {len([v for v in cr_values if v is not None])} papers)")
    print(f"  ORR - Mean: {orr_mean}, Median: {orr_median} (from {len([v for v in orr_values if v is not None])} papers)")
    print(f"  PFS - Mean: {pfs_mean}, Median: {pfs_median} (from {len([v for v in pfs_values if v is not None])} papers)")
    print(f"  OS - Mean: {os_mean}, Median: {os_median} (from {len([v for v in os_values if v is not None])} papers)")
    
    return {
        'efficacy': {
            'cr_mean': cr_mean,
            'cr_median': cr_median,
            'orr_mean': orr_mean,
            'orr_median': orr_median
        },
        'survival': {
            'pfs_mean': pfs_mean,
            'pfs_median': pfs_median,
            'os_mean': os_mean,
            'os_median': os_median
        }
    }

def analyze_decitabine_data():
    """Analyze Decitabine clinical efficacy data"""
    with open('Decitabine_extracted.json', 'r') as f:
        data = json.load(f)
    
    papers_with_data = [p for p in data if p.get('has_efficacy_data')]
    
    # Extract values
    cr_values = [extract_numeric_value(p.get('complete_response')) for p in papers_with_data]
    orr_values = [extract_numeric_value(p.get('overall_response_rate')) for p in papers_with_data]
    pfs_values = [extract_numeric_value(p.get('progression_free_survival_median')) for p in papers_with_data]
    os_values = [extract_numeric_value(p.get('overall_survival_median')) for p in papers_with_data]
    
    # Calculate statistics
    cr_mean, cr_median = calculate_statistics(cr_values)
    orr_mean, orr_median = calculate_statistics(orr_values)
    pfs_mean, pfs_median = calculate_statistics(pfs_values)
    os_mean, os_median = calculate_statistics(os_values)
    
    print(f"\nDecitabine Analysis:")
    print(f"  Papers with efficacy data: {len(papers_with_data)}")
    print(f"  CR - Mean: {cr_mean}, Median: {cr_median} (from {len([v for v in cr_values if v is not None])} papers)")
    print(f"  ORR - Mean: {orr_mean}, Median: {orr_median} (from {len([v for v in orr_values if v is not None])} papers)")
    print(f"  PFS - Mean: {pfs_mean}, Median: {pfs_median} (from {len([v for v in pfs_values if v is not None])} papers)")
    print(f"  OS - Mean: {os_mean}, Median: {os_median} (from {len([v for v in os_values if v is not None])} papers)")
    
    return {
        'efficacy': {
            'cr_mean': cr_mean,
            'cr_median': cr_median,
            'orr_mean': orr_mean,
            'orr_median': orr_median
        },
        'survival': {
            'pfs_mean': pfs_mean,
            'pfs_median': pfs_median,
            'os_mean': os_mean,
            'os_median': os_median
        }
    }

def analyze_hydroxyurea_data():
    """Analyze Hydroxyurea clinical efficacy data"""
    with open('Hydroxyurea_extracted.json', 'r') as f:
        data = json.load(f)
    
    papers_with_data = [p for p in data if p.get('has_efficacy_data')]
    
    # Extract values
    cr_values = [extract_numeric_value(p.get('complete_response')) for p in papers_with_data]
    orr_values = [extract_numeric_value(p.get('overall_response_rate')) for p in papers_with_data]
    pfs_values = [extract_numeric_value(p.get('progression_free_survival_median')) for p in papers_with_data]
    os_values = [extract_numeric_value(p.get('overall_survival_median')) for p in papers_with_data]
    
    # Calculate statistics
    cr_mean, cr_median = calculate_statistics(cr_values)
    orr_mean, orr_median = calculate_statistics(orr_values)
    pfs_mean, pfs_median = calculate_statistics(pfs_values)
    os_mean, os_median = calculate_statistics(os_values)
    
    print(f"\nHydroxyurea Analysis:")
    print(f"  Papers with efficacy data: {len(papers_with_data)}")
    print(f"  CR - Mean: {cr_mean}, Median: {cr_median} (from {len([v for v in cr_values if v is not None])} papers)")
    print(f"  ORR - Mean: {orr_mean}, Median: {orr_median} (from {len([v for v in orr_values if v is not None])} papers)")
    print(f"  PFS - Mean: {pfs_mean}, Median: {pfs_median} (from {len([v for v in pfs_values if v is not None])} papers)")
    print(f"  OS - Mean: {os_mean}, Median: {os_median} (from {len([v for v in os_values if v is not None])} papers)")
    
    return {
        'efficacy': {
            'cr_mean': cr_mean,
            'cr_median': cr_median,
            'orr_mean': orr_mean,
            'orr_median': orr_median
        },
        'survival': {
            'pfs_mean': pfs_mean,
            'pfs_median': pfs_median,
            'os_mean': os_mean,
            'os_median': os_median
        }
    }

def count_unique_papers():
    """Count unique papers across all datasets"""
    all_pmids = set()
    drug_pmids = defaultdict(set)
    
    # Azacitidine
    with open('clinical_efficacy_azacitidine.json', 'r') as f:
        data = json.load(f)
    for paper in data:
        pmid = paper.get('pmid')
        if pmid:
            all_pmids.add(pmid)
            drug_pmids['azacitidine'].add(pmid)
    
    # Decitabine
    with open('Decitabine_extracted.json', 'r') as f:
        data = json.load(f)
    for paper in data:
        pmid = paper.get('pmid')
        if pmid:
            all_pmids.add(pmid)
            drug_pmids['decitabine'].add(pmid)
    
    # Hydroxyurea
    with open('Hydroxyurea_extracted.json', 'r') as f:
        data = json.load(f)
    for paper in data:
        pmid = paper.get('pmid')
        if pmid:
            all_pmids.add(pmid)
            drug_pmids['hydroxyurea'].add(pmid)
    
    print(f"\nUnique Paper Counts:")
    print(f"  Azacitidine: {len(drug_pmids['azacitidine'])} unique papers")
    print(f"  Decitabine: {len(drug_pmids['decitabine'])} unique papers")
    print(f"  Hydroxyurea: {len(drug_pmids['hydroxyurea'])} unique papers")
    print(f"  Total unique papers: {len(all_pmids)}")
    
    return {
        'azacitidine': len(drug_pmids['azacitidine']),
        'decitabine': len(drug_pmids['decitabine']),
        'hydroxyurea': len(drug_pmids['hydroxyurea']),
        'total_unique': len(all_pmids)
    }

def update_dashboard_data():
    """Update the dashboard data with corrected statistics"""
    
    # Analyze data
    azacitidine_stats = analyze_azacitidine_data()
    decitabine_stats = analyze_decitabine_data()
    hydroxyurea_stats = analyze_hydroxyurea_data()
    unique_counts = count_unique_papers()
    
    # Load current dashboard data
    with open('updated_dashboard_data.json', 'r') as f:
        dashboard_data = json.load(f)
    
    # Update statistics
    dashboard_data['azacitidine'].update(azacitidine_stats)
    dashboard_data['decitabine'].update(decitabine_stats)
    dashboard_data['hydroxyurea'].update(hydroxyurea_stats)
    
    # Update paper counts
    dashboard_data['_metadata']['comprehensive_paper_counts'] = {
        'azacitidine': unique_counts['azacitidine'],
        'decitabine': unique_counts['decitabine'],
        'hydroxyurea': unique_counts['hydroxyurea'],
        'total_comprehensive': unique_counts['total_unique']
    }
    
    # Save updated data
    with open('updated_dashboard_data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    
    print(f"\n✅ Updated dashboard data with corrected statistics!")

if __name__ == "__main__":
    update_dashboard_data()
