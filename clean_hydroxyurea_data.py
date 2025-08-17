#!/usr/bin/env python3
"""
Clean hydroxyurea data by removing papers that don't actually contain hydroxyurea treatment data
"""

import json

def clean_hydroxyurea_data():
    # Load the hydroxyurea data
    with open('Hydroxyurea_extracted.json', 'r') as f:
        data = json.load(f)
    
    print(f"Original hydroxyurea papers: {len(data)}")
    
    # Filter out papers that don't contain hydroxyurea treatment data
    cleaned_data = []
    removed_count = 0
    
    for paper in data:
        pmid = paper.get('pmid')
        citation = paper.get('citation', '').lower()
        abstract = paper.get('abstract', '').lower()
        
        # Check if this paper contains hydroxyurea treatment data
        has_hydroxyurea = 'hydroxyurea' in citation or 'hydroxyurea' in abstract
        has_hu = ' hu ' in citation or ' hu ' in abstract
        
        if has_hydroxyurea or has_hu:
            cleaned_data.append(paper)
        else:
            removed_count += 1
            print(f"Removing PMID {pmid}: No hydroxyurea treatment data")
    
    print(f"Removed {removed_count} papers without hydroxyurea treatment data")
    print(f"Cleaned hydroxyurea papers: {len(cleaned_data)}")
    
    # Save the cleaned data
    with open('Hydroxyurea_extracted_cleaned.json', 'w') as f:
        json.dump(cleaned_data, f, indent=2)
    
    print("Cleaned data saved to Hydroxyurea_extracted_cleaned.json")
    
    # Update the original file
    with open('Hydroxyurea_extracted.json', 'w') as f:
        json.dump(cleaned_data, f, indent=2)
    
    print("Original file updated with cleaned data")

if __name__ == "__main__":
    clean_hydroxyurea_data()
