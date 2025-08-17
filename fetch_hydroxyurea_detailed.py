#!/usr/bin/env python3
"""
Fetch detailed abstracts for hydroxyurea CMML papers
"""

import requests
import time
import json
import re

def fetch_detailed_abstracts():
    # Load the comprehensive papers
    with open('pubmed_hydroxyurea_cmml_comprehensive.json', 'r') as f:
        papers = json.load(f)
    
    print(f"Fetching detailed abstracts for {len(papers)} papers...")
    
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    for i, paper in enumerate(papers):
        pmid = paper['pmid']
        print(f"\n{i+1}. Processing PMID {pmid}: {paper['title'][:60]}...")
        
        # Fetch detailed abstract using MEDLINE format
        try:
            fetch_url = f"{base_url}efetch.fcgi"
            fetch_params = {
                'db': 'pubmed',
                'id': pmid,
                'retmode': 'text',
                'rettype': 'medline'
            }
            fetch_response = requests.get(fetch_url, params=fetch_params)
            
            if fetch_response.status_code == 200:
                text = fetch_response.text
                # Extract abstract using regex
                abstract_match = re.search(r'AB\s+-\s+(.*?)(?=\n[A-Z]{2}\s+-|\n\n|\Z)', text, re.DOTALL)
                if abstract_match:
                    abstract = abstract_match.group(1).strip()
                    # Clean up the abstract
                    abstract = re.sub(r'\s+', ' ', abstract)  # Replace multiple spaces with single space
                    paper['abstract'] = abstract
                    print(f"   ✓ Abstract found: {len(abstract)} chars")
                else:
                    print(f"   ✗ No abstract found")
            else:
                print(f"   ✗ Failed to fetch: HTTP {fetch_response.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        time.sleep(1)  # Rate limiting
    
    # Save the enhanced papers
    output_file = 'pubmed_hydroxyurea_cmml_detailed.json'
    with open(output_file, 'w') as f:
        json.dump(papers, f, indent=2)
    
    print(f"\n💾 Saved detailed papers to {output_file}")
    
    # Show summary
    print(f"\n📋 Final papers with detailed abstracts:")
    for i, paper in enumerate(papers):
        abstract_length = len(paper.get('abstract', ''))
        print(f"{i+1}. PMID {paper['pmid']}: {paper['title']}")
        print(f"   Abstract: {abstract_length} characters")

if __name__ == "__main__":
    fetch_detailed_abstracts()
