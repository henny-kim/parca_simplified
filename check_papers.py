#!/usr/bin/env python3
import json

def check_papers():
    with open('Hydroxyurea_extracted.json', 'r') as f:
        data = json.load(f)
    
    efficacy_papers = [p for p in data if p.get('has_efficacy_data')]
    
    print("Papers with efficacy data:")
    print("=" * 50)
    
    for i, paper in enumerate(efficacy_papers, 1):
        pmid = paper['pmid']
        citation = paper['citation']
        abstract = paper.get('abstract', '')[:200] + '...' if paper.get('abstract') else 'No abstract'
        
        print(f"{i}. PMID {pmid}")
        print(f"   Citation: {citation}")
        print(f"   Abstract: {abstract}")
        
        # Check if this paper is actually about hydroxyurea treatment
        citation_lower = citation.lower()
        abstract_lower = abstract.lower()
        
        has_hydroxyurea = 'hydroxyurea' in citation_lower or 'hydroxyurea' in abstract_lower
        has_hu = ' hu ' in citation_lower or ' hu ' in abstract_lower
        
        if has_hydroxyurea or has_hu:
            print("   ✅ CONTAINS HYDROXYUREA")
        else:
            print("   ❌ NO HYDROXYUREA MENTIONED")
        
        print("-" * 50)

if __name__ == "__main__":
    check_papers()
