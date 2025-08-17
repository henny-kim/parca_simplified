#!/usr/bin/env python3
"""
Fetch detailed abstracts for decitabine CMML papers to extract adverse events
"""

import requests
import time
import json
import re

def fetch_decitabine_abstracts():
    # Load the decitabine papers
    with open('Decitabine_extracted.json', 'r') as f:
        papers = json.load(f)
    
    print(f"Fetching detailed abstracts for {len(papers)} decitabine papers...")
    
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    for i, paper in enumerate(papers):
        pmid = paper['pmid']
        print(f"\n{i+1}. Processing PMID {pmid}: {paper.get('title', 'No title')[:60]}...")
        
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
    output_file = 'Decitabine_extracted_with_abstracts.json'
    with open(output_file, 'w') as f:
        json.dump(papers, f, indent=2)
    
    print(f"\n💾 Saved papers with abstracts to {output_file}")
    
    # Show summary
    papers_with_abstracts = sum(1 for p in papers if p.get('abstract'))
    print(f"\n📋 Summary:")
    print(f"Total papers: {len(papers)}")
    print(f"Papers with abstracts: {papers_with_abstracts}")
    print(f"Abstract success rate: {papers_with_abstracts/len(papers)*100:.1f}%")

if __name__ == "__main__":
    fetch_decitabine_abstracts()
