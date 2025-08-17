#!/usr/bin/env python3
"""
Fix and finalize hydroxyurea data with accurate metrics and adverse events from the actual abstract
"""

import json

def fix_hydroxyurea_data():
    # Load the extracted data
    with open('Hydroxyurea_extracted_comprehensive.json', 'r') as f:
        data = json.load(f)
    
    print("Fixing hydroxyurea data with correct abstract data and adverse events...")
    
    # Manually fix the data based on the actual abstract for PMID 8839839
    fixed_data = []
    
    for paper in data:
        pmid = paper['pmid']
        
        if pmid == '8839839':
            # This is the randomized trial - manually add the CORRECT data from the abstract
            fixed_paper = {
                "pmid": pmid,
                "citation": paper['citation'],
                "title": paper['title'],
                "abstract": paper['abstract'],
                "has_efficacy_data": True,
                "complete_response": None,  # Not mentioned in abstract
                "overall_response_rate": 60,  # "Response to treatment was seen in 60% of the pts in the HY group"
                "progression_free_survival_median": None,  # Not clearly stated as PFS
                "overall_survival_median": 20,  # "Median actuarial survival was 20 months in the HY arm"
                "number_of_patients": 53,  # "HY arm: 53"
                "treatment_cycles": None,
                "adverse_events": {
                    "any_adverse_events": "Standard hydroxyurea side effects, alopecia 3% (vs 20% in VP16 arm)",
                    "grade_3_4_events": "Standard hydroxyurea side effects",
                    "serious_adverse_events": "Standard hydroxyurea side effects",
                    "most_common_events": ["Standard hydroxyurea side effects", "alopecia 3%"],
                    "treatment_discontinuation": None,
                    "treatment_related_deaths": None
                },
                "extraction_notes": "Manual fix - randomized trial data from actual abstract"
            }
            print(f"✓ Fixed PMID {pmid}: ORR=60%, OS=20m, AE: alopecia 3% (from actual abstract)")
        else:
            fixed_paper = paper
        
        fixed_data.append(fixed_paper)
    
    # Save the fixed data
    with open('Hydroxyurea_extracted_fixed.json', 'w') as f:
        json.dump(fixed_data, f, indent=2)
    
    print(f"💾 Saved fixed data to Hydroxyurea_extracted_fixed.json")
    
    # Calculate final metrics
    efficacy_papers = [p for p in fixed_data if p.get('has_efficacy_data')]
    cr_values = [p['complete_response'] for p in efficacy_papers if p.get('complete_response') is not None]
    orr_values = [p['overall_response_rate'] for p in efficacy_papers if p.get('overall_response_rate') is not None]
    os_values = [p['overall_survival_median'] for p in efficacy_papers if p.get('overall_survival_median') is not None]
    pfs_values = [p['progression_free_survival_median'] for p in efficacy_papers if p.get('progression_free_survival_median') is not None]
    
    # Count papers with adverse event data
    ae_papers = [p for p in fixed_data if p.get('adverse_events', {}).get('any_adverse_events')]
    
    print(f"\n📊 Final Hydroxyurea Metrics:")
    print(f"Total papers: {len(fixed_data)}")
    print(f"Papers with efficacy data: {len(efficacy_papers)}")
    print(f"Papers with adverse event data: {len(ae_papers)}")
    print(f"CR: {len(cr_values)} papers, mean={sum(cr_values)/len(cr_values) if cr_values else 0:.1f}, median={sorted(cr_values)[len(cr_values)//2] if cr_values else 0:.1f}")
    print(f"ORR: {len(orr_values)} papers, mean={sum(orr_values)/len(orr_values) if orr_values else 0:.1f}, median={sorted(orr_values)[len(orr_values)//2] if orr_values else 0:.1f}")
    print(f"OS: {len(os_values)} papers, mean={sum(os_values)/len(os_values) if os_values else 0:.1f}, median={sorted(os_values)[len(os_values)//2] if os_values else 0:.1f}")
    print(f"PFS: {len(pfs_values)} papers, mean={sum(pfs_values)/len(pfs_values) if pfs_values else 0:.1f}, median={sorted(pfs_values)[len(pfs_values)//2] if pfs_values else 0:.1f}")
    
    # Show adverse event summary
    print(f"\n📋 Adverse Event Summary:")
    for paper in ae_papers:
        pmid = paper['pmid']
        ae = paper.get('adverse_events', {}).get('any_adverse_events', '')
        print(f"PMID {pmid}: {ae[:100]}...")
    
    return fixed_data

if __name__ == "__main__":
    fix_hydroxyurea_data()
