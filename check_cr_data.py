#!/usr/bin/env python3
"""
Check for CR data in original hydroxyurea papers
"""

import json

def check_cr_data():
    # Check original dataset
    try:
        with open('pubmed_hydroxyurea_cmml.json', 'r') as f:
            original_data = json.load(f)
        print(f"Original dataset: {len(original_data)} papers")
    except:
        print("Original dataset not found")
        return
    
    # Check if any papers have CR data
    cr_papers = []
    for paper in original_data:
        if 'complete_response' in str(paper):
            cr_value = paper.get('complete_response')
            if cr_value and cr_value > 0:
                cr_papers.append(paper)
    
    print(f"Papers with CR > 0: {len(cr_papers)}")
    for paper in cr_papers:
        print(f"PMID {paper['pmid']}: CR={paper.get('complete_response')}%")
    
    # Check current dataset
    try:
        with open('Hydroxyurea_extracted.json', 'r') as f:
            current_data = json.load(f)
        print(f"\nCurrent dataset: {len(current_data)} papers")
        
        efficacy_papers = [p for p in current_data if p.get('has_efficacy_data')]
        print(f"Papers with efficacy data: {len(efficacy_papers)}")
        
        cr_values = [p.get('complete_response') for p in efficacy_papers if p.get('complete_response') is not None]
        print(f"CR values found: {cr_values}")
        
    except Exception as e:
        print(f"Error reading current dataset: {e}")

if __name__ == "__main__":
    check_cr_data()
