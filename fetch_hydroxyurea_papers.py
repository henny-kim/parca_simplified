#!/usr/bin/env python3
"""
Fetch Hydroxyurea Papers from PubMed for CMML Treatment
"""

import json
import time
import requests
import re
from typing import List, Dict, Any

def search_pubmed(query: str, max_results: int = 100) -> List[Dict[str, Any]]:
    """Search PubMed and return results."""
    
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    # Search for papers
    search_url = f"{base_url}esearch.fcgi"
    search_params = {
        'db': 'pubmed',
        'term': query,
        'retmax': max_results,
        'retmode': 'json',
        'sort': 'relevance'
    }
    
    try:
        response = requests.get(search_url, params=search_params)
        response.raise_for_status()
        search_data = response.json()
        
        # Extract PMIDs
        id_list = search_data.get('esearchresult', {}).get('idlist', [])
        print(f"Found {len(id_list)} papers for query: {query}")
        
        if not id_list:
            return []
        
        # Fetch details for each paper
        papers = []
        batch_size = 20  # Process in batches to avoid overwhelming the API
        
        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i:i + batch_size]
            
            # Fetch summary data
            summary_url = f"{base_url}esummary.fcgi"
            summary_params = {
                'db': 'pubmed',
                'id': ','.join(batch_ids),
                'retmode': 'json'
            }
            
            response = requests.get(summary_url, params=summary_params)
            response.raise_for_status()
            summary_data = response.json()
            
            # Process each paper
            for pmid in batch_ids:
                if pmid in summary_data.get('result', {}):
                    paper_data = summary_data['result'][pmid]
                    
                    # Extract relevant information
                    paper = {
                        'pmid': pmid,
                        'title': paper_data.get('title', ''),
                        'abstract': '',  # Will be filled below
                        'journal': paper_data.get('fulljournalname', ''),
                        'publication_date': paper_data.get('pubdate', ''),
                        'authors': paper_data.get('authors', []),
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        'citation': f"{paper_data.get('authors', ['Unknown'])[0] if paper_data.get('authors') else 'Unknown'} et al. {paper_data.get('title', '')}. {paper_data.get('fulljournalname', '')} ({paper_data.get('pubdate', '')})",
                        'drug': 'hydroxyurea'
                    }
                    
                    # Fetch abstract using MEDLINE format
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
                            else:
                                print(f"No abstract found for PMID {pmid}")
                        else:
                            print(f"Failed to fetch abstract for PMID {pmid}: HTTP {fetch_response.status_code}")
                    except Exception as e:
                        print(f"Could not fetch abstract for PMID {pmid}: {e}")
                    
                    papers.append(paper)
            
            # Rate limiting
            time.sleep(1)
        
        return papers
        
    except Exception as e:
        print(f"Error searching PubMed: {e}")
        return []

def main():
    # Search queries for hydroxyurea and CMML
    search_queries = [
        "chronic myelomonocytic leukemia hydroxyurea",
        "CMML hydroxyurea treatment", 
        "hydroxyurea chronic myelomonocytic leukemia",
        "CMML HU therapy",
        "myelomonocytic leukemia hydroxyurea"
    ]
    
    all_papers = []
    seen_pmids = set()
    
    for query in search_queries:
        print(f"\nSearching for: {query}")
        papers = search_pubmed(query, max_results=50)
        
        # Deduplicate by PMID
        for paper in papers:
            if paper['pmid'] not in seen_pmids:
                all_papers.append(paper)
                seen_pmids.add(paper['pmid'])
        
        print(f"Total unique papers so far: {len(all_papers)}")
        time.sleep(2)  # Rate limiting between searches
    
    # Save results
    output_data = {
        'hydroxyurea': all_papers
    }
    
    with open('pubmed_hydroxyurea_cmml.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nSaved {len(all_papers)} unique hydroxyurea papers to pubmed_hydroxyurea_cmml.json")
    
    # Summary
    with_abstracts = len([p for p in all_papers if p.get('abstract')])
    print(f"Papers with abstracts: {with_abstracts}/{len(all_papers)} ({with_abstracts/len(all_papers)*100:.1f}%)")

if __name__ == "__main__":
    main()
