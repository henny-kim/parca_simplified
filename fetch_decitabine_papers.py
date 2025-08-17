#!/usr/bin/env python3
"""
Script to fetch papers from PubMed search for "chronic myelomonocytic leukemia Decitabine"
and prepare them for adverse event extraction
"""

import requests
import json
import time
import os
from typing import List, Dict, Any
from urllib.parse import quote

class PubMedFetcher:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.tool = "CMML_Research"
        self.email = "research@example.com"
        
    def search_pubmed(self, query: str, max_results: int = 100) -> List[str]:
        """Search PubMed and return PMIDs"""
        search_url = f"{self.base_url}/esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'tool': self.tool,
            'email': self.email
        }
        
        try:
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'esearchresult' in data and 'idlist' in data['esearchresult']:
                return data['esearchresult']['idlist']
            else:
                print("No results found or unexpected response format")
                return []
                
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []
    
    def fetch_paper_details(self, pmid: str) -> Dict[str, Any]:
        """Fetch detailed information for a single paper"""
        fetch_url = f"{self.base_url}/efetch.fcgi"
        params = {
            'db': 'pubmed',
            'id': pmid,
            'retmode': 'xml',
            'tool': self.tool,
            'email': self.email
        }
        
        try:
            response = requests.get(fetch_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Extract basic information
            paper_data = {
                'pmid': pmid,
                'title': '',
                'authors': [],
                'journal': '',
                'publication_date': '',
                'abstract': '',
                'pmcid': None,
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            }
            
            # Extract title
            title_elem = root.find(".//ArticleTitle")
            if title_elem is not None:
                paper_data['title'] = title_elem.text or ''
            
            # Extract authors
            author_list = root.find(".//AuthorList")
            if author_list is not None:
                for author in author_list.findall("Author"):
                    last_name = author.find("LastName")
                    fore_name = author.find("ForeName")
                    if last_name is not None and fore_name is not None:
                        paper_data['authors'].append(f"{fore_name.text} {last_name.text}")
            
            # Extract journal info
            journal_elem = root.find(".//Journal/Title")
            if journal_elem is not None:
                paper_data['journal'] = journal_elem.text or ''
            
            # Extract publication date
            pub_date = root.find(".//PubDate")
            if pub_date is not None:
                year = pub_date.find("Year")
                month = pub_date.find("Month")
                if year is not None:
                    date_parts = [year.text]
                    if month is not None:
                        date_parts.append(month.text)
                    paper_data['publication_date'] = ' '.join(date_parts)
            
            # Extract abstract
            abstract_elem = root.find(".//Abstract/AbstractText")
            if abstract_elem is not None:
                paper_data['abstract'] = abstract_elem.text or ''
            
            # Extract PMCID if available
            pmcid_elem = root.find(".//ArticleIdList/ArticleId[@IdType='pmc']")
            if pmcid_elem is not None:
                paper_data['pmcid'] = pmcid_elem.text
            
            # Create citation
            if paper_data['authors']:
                first_author = paper_data['authors'][0]
                paper_data['citation'] = f"{first_author} et al. {paper_data['title']}. {paper_data['journal']} ({paper_data['publication_date']})"
            else:
                paper_data['citation'] = f"{paper_data['title']}. {paper_data['journal']} ({paper_data['publication_date']})"
            
            return paper_data
            
        except Exception as e:
            print(f"Error fetching details for PMID {pmid}: {e}")
            return {
                'pmid': pmid,
                'title': '',
                'authors': [],
                'journal': '',
                'publication_date': '',
                'abstract': '',
                'pmcid': None,
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                'citation': f"PMID {pmid}"
            }
    
    def fetch_multiple_papers(self, pmids: List[str], delay: float = 0.1) -> List[Dict[str, Any]]:
        """Fetch details for multiple papers with rate limiting"""
        papers = []
        
        for i, pmid in enumerate(pmids):
            print(f"Fetching paper {i+1}/{len(pmids)}: PMID {pmid}")
            paper_data = self.fetch_paper_details(pmid)
            papers.append(paper_data)
            
            # Rate limiting
            time.sleep(delay)
        
        return papers

def main():
    """Main function to fetch papers from PubMed search"""
    
    fetcher = PubMedFetcher()
    
    # Search for "chronic myelomonocytic leukemia Decitabine" papers
    query = "chronic myelomonocytic leukemia Decitabine"
    print(f"Searching PubMed for: {query}")
    
    pmids = fetcher.search_pubmed(query, max_results=200)  # Get all available papers
    
    if not pmids:
        print("No PMIDs found")
        return
    
    print(f"Found {len(pmids)} papers")
    
    # Fetch detailed information for each paper
    papers = fetcher.fetch_multiple_papers(pmids)
    
    # Organize papers by drug (all will be decitabine for this search)
    organized_data = {
        'decitabine': []
    }
    
    for paper in papers:
        # Add fields expected by the adverse event extractor
        paper_data = {
            'pmid': paper['pmid'],
            'citation': paper['citation'],
            'url': paper['url'],
            'pmcid': paper['pmcid'],
            'title': paper['title'],
            'abstract': paper['abstract'],
            'journal': paper['journal'],
            'publication_date': paper['publication_date'],
            'authors': paper['authors'],
            # Add placeholder fields for compatibility
            'complete_response': None,
            'partial_response': None,
            'marrow_complete_response': None,
            'marrow_optimal_response': None,
            'pfs_median': None,
            'os_median': None,
            'efs_median': None,
            'sae_frequency': None,
            'key_findings': paper['abstract'],  # Use abstract as key findings
            'study_design': '',
            'patient_population': '',
            'treatment_details': '',
            'supporting_quotes': [],
            'data_source_location': 'PubMed Search',
            'reference_note': f"Fetched from PubMed search: {query}",
            'verification_url': paper['url']
        }
        
        organized_data['decitabine'].append(paper_data)
    
    # Save the fetched data
    output_file = 'pubmed_decitabine_cmml.json'
    with open(output_file, 'w') as f:
        json.dump(organized_data, f, indent=2)
    
    print(f"\nFetched {len(papers)} papers and saved to {output_file}")
    
    # Print summary
    papers_with_abstract = sum(1 for paper in papers if paper['abstract'])
    papers_with_pmcid = sum(1 for paper in papers if paper['pmcid'])
    
    print(f"Papers with abstracts: {papers_with_abstract}/{len(papers)}")
    print(f"Papers with PMC ID: {papers_with_pmcid}/{len(papers)}")
    
    # Show some examples
    print("\nSample papers:")
    for i, paper in enumerate(papers[:3]):
        print(f"{i+1}. {paper['citation']}")
        if paper['abstract']:
            print(f"   Abstract: {paper['abstract'][:200]}...")
        print()

if __name__ == "__main__":
    main()
