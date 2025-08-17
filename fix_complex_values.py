#!/usr/bin/env python3
"""
Fix complex object values in the data that are causing [object Object]% display issues
"""

import json
import statistics

def extract_single_value(value):
    """Extract a single numeric value from complex data structures"""
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
        # For cases like {'DEC-C': 64.0, 'DEC-C-Ven': 90.0}
        # Take the average of all numeric values
        values = [v for v in value.values() if isinstance(v, (int, float))]
        if values:
            return statistics.mean(values)
        return None
    if isinstance(value, list):
        # For cases where it's a list of numbers
        values = [v for v in value if isinstance(v, (int, float))]
        if values:
            return statistics.mean(values)
        return None
    return None

def clean_decitabine_data():
    """Clean the Decitabine data to fix complex object values"""
    with open('Decitabine_extracted.json', 'r') as f:
        data = json.load(f)
    
    cleaned_data = []
    for paper in data:
        cleaned_paper = paper.copy()
        
        # Clean ORR values
        if 'overall_response_rate' in cleaned_paper:
            cleaned_paper['overall_response_rate'] = extract_single_value(cleaned_paper['overall_response_rate'])
        
        # Clean CR values
        if 'complete_response' in cleaned_paper:
            cleaned_paper['complete_response'] = extract_single_value(cleaned_paper['complete_response'])
        
        # Clean survival values
        if 'progression_free_survival_median' in cleaned_paper:
            cleaned_paper['progression_free_survival_median'] = extract_single_value(cleaned_paper['progression_free_survival_median'])
        
        if 'overall_survival_median' in cleaned_paper:
            cleaned_paper['overall_survival_median'] = extract_single_value(cleaned_paper['overall_survival_median'])
        
        cleaned_data.append(cleaned_paper)
    
    # Save cleaned data
    with open('Decitabine_extracted_cleaned.json', 'w') as f:
        json.dump(cleaned_data, f, indent=2)
    
    print(f"✅ Cleaned Decitabine data - saved to Decitabine_extracted_cleaned.json")
    
    # Show examples of cleaned values
    print("\nExamples of cleaned values:")
    for i, paper in enumerate(cleaned_data[:5]):
        if paper.get('overall_response_rate') is not None:
            print(f"  Paper {i+1}: ORR = {paper['overall_response_rate']}%")
    
    return cleaned_data

def update_dashboard_with_cleaned_data():
    """Update dashboard to use cleaned data"""
    
    # Clean the data first
    cleaned_decitabine = clean_decitabine_data()
    
    # Recalculate statistics with cleaned data
    papers_with_data = [p for p in cleaned_decitabine if p.get('has_efficacy_data')]
    
    # Extract values
    cr_values = [p.get('complete_response') for p in papers_with_data if p.get('complete_response') is not None]
    orr_values = [p.get('overall_response_rate') for p in papers_with_data if p.get('overall_response_rate') is not None]
    pfs_values = [p.get('progression_free_survival_median') for p in papers_with_data if p.get('progression_free_survival_median') is not None]
    os_values = [p.get('overall_survival_median') for p in papers_with_data if p.get('overall_survival_median') is not None]
    
    # Calculate statistics
    cr_mean = round(statistics.mean(cr_values), 1) if cr_values else None
    cr_median = round(statistics.median(cr_values), 1) if cr_values else None
    orr_mean = round(statistics.mean(orr_values), 1) if orr_values else None
    orr_median = round(statistics.median(orr_values), 1) if orr_values else None
    pfs_mean = round(statistics.mean(pfs_values), 1) if pfs_values else None
    pfs_median = round(statistics.median(pfs_values), 1) if pfs_values else None
    os_mean = round(statistics.mean(os_values), 1) if os_values else None
    os_median = round(statistics.median(os_values), 1) if os_values else None
    
    print(f"\nUpdated Decitabine Statistics:")
    print(f"  CR - Mean: {cr_mean}, Median: {cr_median} (from {len(cr_values)} papers)")
    print(f"  ORR - Mean: {orr_mean}, Median: {orr_median} (from {len(orr_values)} papers)")
    print(f"  PFS - Mean: {pfs_mean}, Median: {pfs_median} (from {len(pfs_values)} papers)")
    print(f"  OS - Mean: {os_mean}, Median: {os_median} (from {len(os_values)} papers)")
    
    # Update dashboard data
    with open('updated_dashboard_data.json', 'r') as f:
        dashboard_data = json.load(f)
    
    dashboard_data['decitabine']['efficacy'] = {
        'cr_mean': cr_mean,
        'cr_median': cr_median,
        'orr_mean': orr_mean,
        'orr_median': orr_median
    }
    
    dashboard_data['decitabine']['survival'] = {
        'pfs_mean': pfs_mean,
        'pfs_median': pfs_median,
        'os_mean': os_mean,
        'os_median': os_median
    }
    
    # Save updated dashboard data
    with open('updated_dashboard_data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    
    print(f"\n✅ Updated dashboard data with cleaned Decitabine statistics!")

if __name__ == "__main__":
    update_dashboard_with_cleaned_data()
