#!/usr/bin/env python3
"""
Comprehensive hydroxyurea paper fetching for CMML
Fetches papers using multiple search terms to get complete coverage
"""

import requests
import time
import json
import re
from urllib.parse import quote

def search_pubmed_comprehensive():
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    # Multiple search terms to ensure comprehensive coverage
    search_terms = [
        "cmml hydroxyurea",
        "chronic myelomonocytic leukemia hydroxyurea", 
        "CMML hydroxyurea",
        "hydroxyurea chronic myelomonocytic leukemia",
        "hydroxyurea CMML"
    ]
    
    all_pmids = set()
    
    for search_term in search_terms:
        print(f"\nSearching for: '{search_term}'")
        
        # Search for papers
        search_url = f"{base_url}esearch.fcgi"
        search_params = {
            'db': 'pubmed',
            'term': search_term,
            'retmode': 'json',
            'retmax': 1000,  # Get maximum results
            'tool': 'cmml_research',
            'email': 'research@example.com'
        }
        
        try:
            response = requests.get(search_url, params=search_params)
            if response.status_code == 200:
                data = response.json()
                pmids = data['esearchresult'].get('idlist', [])
                print(f"Found {len(pmids)} PMIDs for '{search_term}'")
                all_pmids.update(pmids)
            else:
                print(f"Search failed for '{search_term}': HTTP {response.status_code}")
        except Exception as e:
            print(f"Error searching for '{search_term}': {e}")
        
        time.sleep(1)  # Rate limiting
    
    print(f"\nTotal unique PMIDs found: {len(all_pmids)}")
    return list(all_pmids)

def fetch_paper_details(pmids):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    papers = []
    
    # Process in batches of 20
    batch_size = 20
    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i+batch_size]
        print(f"\nProcessing batch {i//batch_size + 1}/{(len(pmids) + batch_size - 1)//batch_size}")
        
        # Fetch summaries
        summary_url = f"{base_url}esummary.fcgi"
        summary_params = {
            'db': 'pubmed',
            'id': ','.join(batch),
            'retmode': 'json',
            'tool': 'cmml_research',
            'email': 'research@example.com'
        }
        
        try:
            response = requests.get(summary_url, params=summary_params)
            if response.status_code == 200:
                data = response.json()
                
                for pmid in batch:
                    if pmid in data['result']:
                        paper_info = data['result'][pmid]
                        
                        # Create paper object
                        paper = {
                            'pmid': pmid,
                            'title': paper_info.get('title', ''),
                            'journal': paper_info.get('fulljournalname', ''),
                            'pubdate': paper_info.get('pubdate', ''),
                            'authors': paper_info.get('authors', []),
                            'abstract': paper_info.get('abstract', ''),
                            'citation': paper_info.get('title', '')
                        }
                        
                        # Format citation
                        if paper['authors']:
                            first_author = paper['authors'][0].get('name', '')
                            paper['citation'] = f"{first_author} et al. {paper['title']}. {paper['journal']} ({paper['pubdate']})"
                        
                        papers.append(paper)
                        print(f"  ✓ PMID {pmid}: {paper['title'][:60]}...")
                    else:
                        print(f"  ✗ PMID {pmid}: Not found in results")
            else:
                print(f"Failed to fetch summaries: HTTP {response.status_code}")
        except Exception as e:
            print(f"Error fetching summaries: {e}")
        
        time.sleep(1)  # Rate limiting
    
    return papers

def filter_hydroxyurea_papers(papers):
    """Filter papers to ensure they actually contain hydroxyurea treatment data"""
    filtered_papers = []
    
    for paper in papers:
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        citation = paper.get('citation', '').lower()
        
        # Check for hydroxyurea mentions
        has_hydroxyurea = ('hydroxyurea' in title or 'hydroxyurea' in abstract or 
                          'hydroxyurea' in citation)
        has_hu = (' hu ' in title or ' hu ' in abstract or ' hu ' in citation)
        
        # Check for CMML mentions
        has_cmml = ('cmml' in title or 'cmml' in abstract or 'cmml' in citation or
                   'chronic myelomonocytic' in title or 'chronic myelomonocytic' in abstract or 
                   'chronic myelomonocytic' in citation)
        
        if (has_hydroxyurea or has_hu) and has_cmml:
            filtered_papers.append(paper)
            print(f"✓ Keeping PMID {paper['pmid']}: Contains hydroxyurea + CMML")
        else:
            print(f"✗ Filtering PMID {paper['pmid']}: Missing hydroxyurea or CMML")
    
    return filtered_papers

def main():
    print("🔍 Comprehensive Hydroxyurea CMML Paper Fetching")
    print("=" * 60)
    
    # Step 1: Search for papers
    pmids = search_pubmed_comprehensive()
    
    if not pmids:
        print("No PMIDs found!")
        return
    
    # Step 2: Fetch paper details
    papers = fetch_paper_details(pmids)
    
    if not papers:
        print("No paper details fetched!")
        return
    
    # Step 3: Filter for hydroxyurea + CMML papers
    print(f"\n🔍 Filtering papers for hydroxyurea + CMML content...")
    filtered_papers = filter_hydroxyurea_papers(papers)
    
    print(f"\n📊 Results:")
    print(f"Total papers found: {len(papers)}")
    print(f"Papers with hydroxyurea + CMML: {len(filtered_papers)}")
    
    # Step 4: Save results
    output_file = 'pubmed_hydroxyurea_cmml_comprehensive.json'
    with open(output_file, 'w') as f:
        json.dump(filtered_papers, f, indent=2)
    
    print(f"\n💾 Saved {len(filtered_papers)} papers to {output_file}")
    
    # Show sample papers
    print(f"\n📋 Sample papers:")
    for i, paper in enumerate(filtered_papers[:5]):
        print(f"{i+1}. PMID {paper['pmid']}: {paper['title']}")

if __name__ == "__main__":
    main()
