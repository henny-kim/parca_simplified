#!/usr/bin/env python3
"""
Script to fetch ALL papers from both PubMed searches:
1. "Azacytidine cmml" (169 results)
2. "chronic myelomonocytic leukemia Decitabine" (125 results)
And prepare them for comprehensive adverse event extraction
"""

import requests
import json
import time
import os
from typing import List, Dict, Any

class ComprehensivePubMedFetcher:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.tool = "CMML_Research"
        self.email = "research@example.com"
        
    def search_pubmed(self, query: str, max_results: int = 500) -> List[str]:
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
                total_count = int(data['esearchresult'].get('count', 0))
                print(f"Total papers found: {total_count}")
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
                authors = []
                for author in author_list.findall("Author"):
                    last_name = author.find("LastName")
                    fore_name = author.find("ForeName")
                    if last_name is not None and fore_name is not None:
                        authors.append(f"{fore_name.text} {last_name.text}")
                paper_data['authors'] = authors
            
            # Extract journal info
            journal_elem = root.find(".//Journal/Title")
            if journal_elem is not None:
                paper_data['journal'] = journal_elem.text or ''
            
            # Extract publication date
            pub_date = root.find(".//PubDate")
            if pub_date is not None:
                year = pub_date.find("Year")
                month = pub_date.find("Month")
                date_parts = []
                if year is not None:
                    date_parts.append(year.text)
                if month is not None:
                    date_parts.append(month.text)
                paper_data['publication_date'] = ' '.join(date_parts)
            
            # Extract abstract (handle multiple AbstractText elements)
            abstract_texts = root.findall(".//Abstract/AbstractText")
            if abstract_texts:
                abstract_parts = []
                for abstract_text in abstract_texts:
                    if abstract_text.text:
                        abstract_parts.append(abstract_text.text)
                paper_data['abstract'] = ' '.join(abstract_parts)
            
            # Extract PMCID if available
            pmcid_elem = root.find(".//ArticleIdList/ArticleId[@IdType='pmc']")
            if pmcid_elem is not None:
                paper_data['pmcid'] = pmcid_elem.text
            
            # Create citation
            if paper_data['authors']:
                first_author = paper_data['authors'][0]
                if len(paper_data['authors']) > 1:
                    citation_authors = f"{first_author} et al."
                else:
                    citation_authors = first_author
            else:
                citation_authors = "Unknown authors"
            
            paper_data['citation'] = f"{citation_authors} {paper_data['title']}. {paper_data['journal']} ({paper_data['publication_date']})"
            
            return paper_data
            
        except Exception as e:
            print(f"Error fetching details for PMID {pmid}: {e}")
            return {
                'pmid': pmid,
                'title': f'Error fetching title for PMID {pmid}',
                'authors': [],
                'journal': '',
                'publication_date': '',
                'abstract': '',
                'pmcid': None,
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                'citation': f"PMID {pmid} (error fetching details)"
            }
    
    def fetch_multiple_papers(self, pmids: List[str], delay: float = 0.15) -> List[Dict[str, Any]]:
        """Fetch details for multiple papers with rate limiting"""
        papers = []
        
        for i, pmid in enumerate(pmids):
            print(f"Fetching paper {i+1}/{len(pmids)}: PMID {pmid}")
            paper_data = self.fetch_paper_details(pmid)
            papers.append(paper_data)
            
            # Rate limiting to be respectful to NCBI servers
            time.sleep(delay)
            
            # Progress update every 25 papers
            if (i + 1) % 25 == 0:
                print(f"Progress: {i+1}/{len(pmids)} papers fetched ({((i+1)/len(pmids)*100):.1f}%)")
        
        return papers

    def prepare_for_ae_extraction(self, paper: Dict[str, Any], drug: str, query: str) -> Dict[str, Any]:
        """Prepare paper data for adverse event extraction"""
        return {
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

def main():
    """Main function to fetch ALL papers from both searches"""
    
    fetcher = ComprehensivePubMedFetcher()
    
    # Define both searches
    searches = [
        {
            'query': 'Azacytidine cmml',
            'drug': 'azacitidine',
            'output_file': 'pubmed_azacitidine_cmml_complete.json'
        },
        {
            'query': 'chronic myelomonocytic leukemia Decitabine',
            'drug': 'decitabine', 
            'output_file': 'pubmed_decitabine_cmml_complete.json'
        }
    ]
    
    all_data = {}
    
    for search_info in searches:
        query = search_info['query']
        drug = search_info['drug']
        output_file = search_info['output_file']
        
        print(f"\n{'='*60}")
        print(f"SEARCHING FOR: {query}")
        print(f"{'='*60}")
        
        # Search PubMed
        pmids = fetcher.search_pubmed(query, max_results=500)
        
        if not pmids:
            print(f"No PMIDs found for {query}")
            continue
        
        print(f"Found {len(pmids)} papers for {drug}")
        
        # Fetch detailed information for each paper
        print(f"Fetching detailed information for {len(pmids)} papers...")
        papers = fetcher.fetch_multiple_papers(pmids)
        
        # Prepare data for adverse event extraction
        prepared_papers = []
        for paper in papers:
            prepared_paper = fetcher.prepare_for_ae_extraction(paper, drug, query)
            prepared_papers.append(prepared_paper)
        
        # Organize by drug
        drug_data = {drug: prepared_papers}
        
        # Save individual drug data
        with open(output_file, 'w') as f:
            json.dump(drug_data, f, indent=2)
        
        print(f"Saved {len(prepared_papers)} papers to {output_file}")
        
        # Add to combined data
        all_data[drug] = prepared_papers
        
        # Print summary
        papers_with_abstract = sum(1 for paper in papers if paper['abstract'])
        papers_with_pmcid = sum(1 for paper in papers if paper['pmcid'])
        
        print(f"Papers with abstracts: {papers_with_abstract}/{len(papers)} ({papers_with_abstract/len(papers)*100:.1f}%)")
        print(f"Papers with PMC ID: {papers_with_pmcid}/{len(papers)} ({papers_with_pmcid/len(papers)*100:.1f}%)")
    
    # Save combined data
    combined_output = 'pubmed_all_cmml_papers.json'
    with open(combined_output, 'w') as f:
        json.dump(all_data, f, indent=2)
    
    # Final summary
    total_papers = sum(len(papers) for papers in all_data.values())
    print(f"\n{'='*60}")
    print(f"FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Total papers fetched: {total_papers}")
    for drug, papers in all_data.items():
        print(f"{drug.capitalize()}: {len(papers)} papers")
    print(f"Combined data saved to: {combined_output}")
    
    # Show sample papers from each drug
    print(f"\nSample papers from each drug:")
    for drug, papers in all_data.items():
        print(f"\n{drug.upper()}:")
        for i, paper in enumerate(papers[:3]):
            print(f"  {i+1}. PMID {paper['pmid']}: {paper['title'][:80]}...")

if __name__ == "__main__":
    main()
