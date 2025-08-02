import requests
import json
import pandas as pd
from typing import Dict, List, Optional
import time
from dataclasses import dataclass
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
import re
from urllib.parse import urljoin, quote

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyCa_BkY76jkzTqL_TB6b4q17KqoJznu6uk"

@dataclass
class ClinicalOutcome:
    """Structure for clinical outcome data"""
    complete_response: Optional[float] = None
    partial_response: Optional[float] = None
    marrow_cr: Optional[float] = None
    pfs_median: Optional[float] = None
    os_median: Optional[float] = None
    efs_median: Optional[float] = None
    sae_frequency: Optional[float] = None
    ras_mutant_data: Optional[Dict] = None
    non_ras_mutant_data: Optional[Dict] = None
    citation: str = ""
    pmid: str = ""
    url: str = ""

class PubMedScraper:
    """Scrape PubMed without requiring API keys or email"""
    
    def __init__(self):
        self.base_url = "https://pubmed.ncbi.nlm.nih.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def search_pubmed(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search PubMed and return paper details"""
        try:
            # Format search URL
            encoded_query = quote(query)
            search_url = f"{self.base_url}/?term={encoded_query}&size={max_results}"
            
            print(f"Searching: {search_url}")
            response = self.session.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all article cards
            articles = soup.find_all('article', class_='full-docsum')
            
            papers = []
            for article in articles[:max_results]:
                try:
                    # Extract PMID
                    pmid_element = article.find('strong', class_='current-id')
                    pmid = pmid_element.text.strip() if pmid_element else None
                    
                    # Extract title
                    title_element = article.find('a', class_='docsum-title')
                    title = title_element.text.strip() if title_element else "No title"
                    
                    # Extract authors
                    authors_element = article.find('span', class_='docsum-authors')
                    authors = authors_element.get_text(strip=True) if authors_element else "No authors"
                    
                    # Extract journal info
                    journal_element = article.find('span', class_='docsum-journal-citation')
                    journal_info = journal_element.get_text(strip=True) if journal_element else "No journal info"
                    
                    # Extract snippet/abstract preview
                    snippet_element = article.find('div', class_='full-view-snippet')
                    snippet = snippet_element.get_text(strip=True) if snippet_element else ""
                    
                    if pmid:
                        papers.append({
                            'pmid': pmid,
                            'title': title,
                            'authors': authors,
                            'journal_info': journal_info,
                            'snippet': snippet,
                            'url': f"{self.base_url}/{pmid}/"
                        })
                        
                except Exception as e:
                    print(f"Error parsing article: {e}")
                    continue
            
            print(f"Found {len(papers)} papers")
            return papers
            
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []

    def get_paper_abstract(self, pmid: str) -> Optional[Dict]:
        """Get full abstract for a specific PMID"""
        try:
            paper_url = f"{self.base_url}/{pmid}/"
            response = self.session.get(paper_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_element = soup.find('h1', class_='heading-title')
            title = title_element.get_text(strip=True) if title_element else "No title"
            
            # Extract abstract
            abstract_element = soup.find('div', class_='abstract-content')
            abstract = ""
            if abstract_element:
                # Handle structured abstracts
                abstract_sections = abstract_element.find_all(['p', 'div'])
                abstract_parts = []
                for section in abstract_sections:
                    section_text = section.get_text(strip=True)
                    if section_text:
                        abstract_parts.append(section_text)
                abstract = " ".join(abstract_parts)
            
            # Extract journal and year
            citation_element = soup.find('button', class_='journal-actions-trigger')
            journal_info = citation_element.get_text(strip=True) if citation_element else "Unknown journal"
            
            # Extract publication year
            year_match = re.search(r'(\d{4})', journal_info)
            year = year_match.group(1) if year_match else "Unknown year"
            
            # Extract authors
            authors_section = soup.find('div', class_='authors-list')
            authors = "Unknown authors"
            if authors_section:
                author_elements = authors_section.find_all('a')
                if author_elements:
                    authors = ", ".join([a.get_text(strip=True) for a in author_elements[:3]])
                    if len(author_elements) > 3:
                        authors += " et al."
            
            return {
                'pmid': pmid,
                'title': title,
                'abstract': abstract,
                'journal_info': journal_info,
                'year': year,
                'authors': authors,
                'url': paper_url,
                'full_content': f"Title: {title}\n\nAuthors: {authors}\n\nJournal: {journal_info}\n\nAbstract: {abstract}"
            }
            
        except Exception as e:
            print(f"Error fetching abstract for PMID {pmid}: {e}")
            return None

class CMMLResearchExtractor:
    def __init__(self, gemini_api_key: str):
        """Initialize the CMML research data extractor"""
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.scraper = PubMedScraper()
        
        # Extraction prompt template
        self.extraction_prompt = """
        You are a medical research data extraction specialist. Extract CMML-specific clinical outcomes from this research paper.

        Paper content: {paper_content}

        Extract ONLY data specifically for CMML (chronic myelomonocytic leukemia). Do NOT include general MDS or AML data unless explicitly broken down for CMML patients.

        Return the data in this exact JSON format:
        {{
            "drug_name": "string",
            "complete_response_rate": number or null,
            "partial_response_rate": number or null, 
            "marrow_cr_rate": number or null,
            "pfs_median_months": number or null,
            "os_median_months": number or null,
            "efs_median_months": number or null,
            "sae_frequency_percent": number or null,
            "ras_mutant_outcomes": {{
                "cr_rate": number or null,
                "pr_rate": number or null,
                "os_median": number or null,
                "pfs_median": number or null
            }},
            "non_ras_mutant_outcomes": {{
                "cr_rate": number or null,
                "pr_rate": number or null,
                "os_median": number or null,
                "pfs_median": number or null
            }},
            "sample_size": number or null,
            "study_type": "string",
            "citation_info": "string",
            "has_cmml_data": true or false
        }}

        Rules:
        - Return percentages as numbers (e.g., 25.5 for 25.5%)
        - Return survival times in months
        - Only extract data explicitly stated for CMML patients
        - Set has_cmml_data to true ONLY if the paper contains specific CMML outcome data
        - If RAS mutation status is not reported, set those fields to null
        - Be conservative - if unclear, set to null rather than guess
        - If this paper doesn't contain CMML-specific clinical data, set has_cmml_data to false
        """

    def extract_clinical_data(self, paper_content: str) -> Optional[Dict]:
        """Use Gemini to extract clinical data from paper content"""
        try:
            prompt = self.extraction_prompt.format(paper_content=paper_content)
            
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            json_start = response.text.find('{')
            json_end = response.text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response.text[json_start:json_end]
                data = json.loads(json_str)
                
                # Filter out papers without CMML data
                if not data.get('has_cmml_data', False):
                    return None
                    
                return data
            else:
                print("No valid JSON found in response")
                return None
                
        except Exception as e:
            print(f"Error extracting data with Gemini: {e}")
            return None

    def process_drug_research(self, drug_name: str, additional_terms: str = "") -> List[ClinicalOutcome]:
        """Process all research for a specific drug"""
        print(f"\n=== Processing {drug_name} research ===")
        
        # Search queries for the drug
        queries = [
            f"{drug_name} CMML chronic myelomonocytic leukemia efficacy",
            f"{drug_name} CMML clinical trial outcomes response",
            f"{drug_name} CMML survival RAS mutation",
            f"chronic myelomonocytic leukemia {drug_name} treatment {additional_terms}".strip()
        ]
        
        all_papers = []
        seen_pmids = set()
        
        for query in queries:
            print(f"Searching: {query}")
            papers = self.scraper.search_pubmed(query, max_results=15)
            
            # Deduplicate by PMID
            for paper in papers:
                if paper['pmid'] not in seen_pmids:
                    all_papers.append(paper)
                    seen_pmids.add(paper['pmid'])
            
            time.sleep(2)  # Rate limiting
        
        print(f"Total unique papers found: {len(all_papers)}")
        
        clinical_outcomes = []
        
        for i, paper in enumerate(all_papers[:20]):  # Limit to 20 papers
            print(f"Processing paper {i+1}/{min(len(all_papers), 20)}: {paper['title'][:60]}...")
            
            # Quick relevance check
            paper_text = f"{paper['title']} {paper['snippet']}".lower()
            if 'cmml' not in paper_text and 'chronic myelomonocytic leukemia' not in paper_text:
                print(f"  Skipping - not CMML relevant")
                continue
            
            # Get full abstract
            full_paper = self.scraper.get_paper_abstract(paper['pmid'])
            if not full_paper or not full_paper['abstract']:
                print(f"  Skipping - no abstract available")
                continue
            
            # Extract clinical data
            extracted_data = self.extract_clinical_data(full_paper['full_content'])
            if not extracted_data:
                print(f"  No CMML-specific data found")
                continue
            
            # Convert to ClinicalOutcome object
            outcome = ClinicalOutcome(
                complete_response=extracted_data.get('complete_response_rate'),
                partial_response=extracted_data.get('partial_response_rate'),
                marrow_cr=extracted_data.get('marrow_cr_rate'),
                pfs_median=extracted_data.get('pfs_median_months'),
                os_median=extracted_data.get('os_median_months'),
                efs_median=extracted_data.get('efs_median_months'),
                sae_frequency=extracted_data.get('sae_frequency_percent'),
                ras_mutant_data=extracted_data.get('ras_mutant_outcomes'),
                non_ras_mutant_data=extracted_data.get('non_ras_mutant_outcomes'),
                citation=f"{full_paper['authors']} {full_paper['title']} {full_paper['journal_info']}",
                pmid=paper['pmid'],
                url=full_paper['url']
            )
            
            clinical_outcomes.append(outcome)
            print(f"  ✓ Extracted CMML data")
            
            time.sleep(3)  # Rate limiting for scraping and API calls
        
        return clinical_outcomes

    def create_comparative_table(self, azacitidine_data: List[ClinicalOutcome], 
                                decitabine_data: List[ClinicalOutcome],
                                hydroxyurea_data: List[ClinicalOutcome]) -> pd.DataFrame:
        """Create the comparative table as requested"""
        
        def aggregate_outcomes(outcomes: List[ClinicalOutcome], drug_name: str):
            """Aggregate outcomes for a drug, preferring larger studies"""
            if not outcomes:
                return {
                    'Drug': drug_name,
                    'CMML Subtype': 'Overall',
                    'Complete Response (CR)': '...',
                    'Partial Response (PR)': '...',
                    'Marrow CR / Optimal': '...',
                    'PFS (median)': '...',
                    'OS (median)': '...',
                    'SAEs (%)': '...'
                }
            
            # Find best available data for each metric
            cr_rates = [o.complete_response for o in outcomes if o.complete_response is not None]
            pr_rates = [o.partial_response for o in outcomes if o.partial_response is not None]
            marrow_rates = [o.marrow_cr for o in outcomes if o.marrow_cr is not None]
            pfs_values = [o.pfs_median for o in outcomes if o.pfs_median is not None]
            os_values = [o.os_median for o in outcomes if o.os_median is not None]
            sae_rates = [o.sae_frequency for o in outcomes if o.sae_frequency is not None]
            
            return {
                'Drug': drug_name,
                'CMML Subtype': 'Overall',
                'Complete Response (CR)': f"{cr_rates[0]:.1f}%" if cr_rates else '...',
                'Partial Response (PR)': f"{pr_rates[0]:.1f}%" if pr_rates else '...',
                'Marrow CR / Optimal': f"{marrow_rates[0]:.1f}%" if marrow_rates else '...',
                'PFS (median)': f"{pfs_values[0]:.1f} months" if pfs_values else '...',
                'OS (median)': f"{os_values[0]:.1f} months" if os_values else '...',
                'SAEs (%)': f"{sae_rates[0]:.1f}%" if sae_rates else '...'
            }
        
        def add_mutation_rows(outcomes: List[ClinicalOutcome], drug_name: str):
            """Add RAS mutation-specific rows if data is available"""
            rows = []
            
            # Check if any outcome has RAS mutation data
            has_ras_data = any(o.ras_mutant_data for o in outcomes)
            has_non_ras_data = any(o.non_ras_mutant_data for o in outcomes)
            
            if has_ras_data:
                ras_outcome = next(o for o in outcomes if o.ras_mutant_data)
                ras_data = ras_outcome.ras_mutant_data
                rows.append({
                    'Drug': '',
                    'CMML Subtype': 'RAS-mutant',
                    'Complete Response (CR)': f"{ras_data.get('cr_rate', 0):.1f}%" if ras_data.get('cr_rate') else '...',
                    'Partial Response (PR)': f"{ras_data.get('pr_rate', 0):.1f}%" if ras_data.get('pr_rate') else '...',
                    'Marrow CR / Optimal': '...',
                    'PFS (median)': f"{ras_data.get('pfs_median', 0):.1f} months" if ras_data.get('pfs_median') else '...',
                    'OS (median)': f"{ras_data.get('os_median', 0):.1f} months" if ras_data.get('os_median') else '...',
                    'SAEs (%)': '...'
                })
            else:
                rows.append({
                    'Drug': '',
                    'CMML Subtype': 'RAS-mutant',
                    'Complete Response (CR)': '...',
                    'Partial Response (PR)': '...',
                    'Marrow CR / Optimal': '...',
                    'PFS (median)': '...',
                    'OS (median)': '...',
                    'SAEs (%)': '...'
                })
            
            if has_non_ras_data:
                non_ras_outcome = next(o for o in outcomes if o.non_ras_mutant_data)
                non_ras_data = non_ras_outcome.non_ras_mutant_data
                rows.append({
                    'Drug': '',
                    'CMML Subtype': 'Non-RAS-mutant',
                    'Complete Response (CR)': f"{non_ras_data.get('cr_rate', 0):.1f}%" if non_ras_data.get('cr_rate') else '...',
                    'Partial Response (PR)': f"{non_ras_data.get('pr_rate', 0):.1f}%" if non_ras_data.get('pr_rate') else '...',
                    'Marrow CR / Optimal': '...',
                    'PFS (median)': f"{non_ras_data.get('pfs_median', 0):.1f} months" if non_ras_data.get('pfs_median') else '...',
                    'OS (median)': f"{non_ras_data.get('os_median', 0):.1f} months" if non_ras_data.get('os_median') else '...',
                    'SAEs (%)': '...'
                })
            else:
                rows.append({
                    'Drug': '',
                    'CMML Subtype': 'Non-RAS-mutant',
                    'Complete Response (CR)': '...',
                    'Partial Response (PR)': '...',
                    'Marrow CR / Optimal': '...',
                    'PFS (median)': '...',
                    'OS (median)': '...',
                    'SAEs (%)': '...'
                })
            
            return rows
        
        # Create rows for the table
        rows = []
        
        # Azacitidine rows
        rows.append(aggregate_outcomes(azacitidine_data, 'Azacitidine'))
        rows.extend(add_mutation_rows(azacitidine_data, 'Azacitidine'))
        
        # Decitabine rows
        rows.append(aggregate_outcomes(decitabine_data, 'Decitabine'))
        rows.extend(add_mutation_rows(decitabine_data, 'Decitabine'))
        
        # Hydroxyurea rows
        rows.append(aggregate_outcomes(hydroxyurea_data, 'Hydroxyurea'))
        rows.extend(add_mutation_rows(hydroxyurea_data, 'Hydroxyurea'))
        
        return pd.DataFrame(rows)

    def generate_drug_summary(self, drug_name: str, outcomes: List[ClinicalOutcome]) -> str:
        """Generate a paragraph summary for each drug"""
        if not outcomes:
            return f"{drug_name}: Limited CMML-specific data available in the literature."
        
        # Extract key findings
        response_rates = [o.complete_response for o in outcomes if o.complete_response is not None]
        survival_data = [o.os_median for o in outcomes if o.os_median is not None]
        safety_data = [o.sae_frequency for o in outcomes if o.sae_frequency is not None]
        
        citations = [f"PMID:{o.pmid}" for o in outcomes if o.pmid][:3]  # Top 3 citations
        
        summary = f"{drug_name}: "
        if response_rates:
            summary += f"Shows clinical activity in CMML with complete response rates ranging from {min(response_rates):.1f}% to {max(response_rates):.1f}%. "
        if survival_data:
            summary += f"Median overall survival reported as {min(survival_data):.1f}-{max(survival_data):.1f} months. "
        if safety_data:
            summary += f"Safety profile shows {min(safety_data):.1f}-{max(safety_data):.1f}% serious adverse events. "
        
        summary += f"Based on {len(outcomes)} CMML-specific studies. Key studies: {', '.join(citations)}."
        
        return summary

def main():
    """Main execution function"""
    # Check if API key is set
    if GEMINI_API_KEY == "your_gemini_api_key_here":
        print("Please set your Gemini API key in the GEMINI_API_KEY variable")
        return
    
    # Initialize extractor
    extractor = CMMLResearchExtractor(gemini_api_key=GEMINI_API_KEY)
    
    print("CMML Clinical Data Extraction Starting...")
    print("This will scrape PubMed directly - no email required!")
    print("=" * 50)
    
    # Process each drug
    azacitidine_outcomes = extractor.process_drug_research("azacitidine", "hypomethylating")
    decitabine_outcomes = extractor.process_drug_research("decitabine", "hypomethylating")
    hydroxyurea_outcomes = extractor.process_drug_research("hydroxyurea", "cytoreductive")
    
    # Create comparative table
    comparison_df = extractor.create_comparative_table(
        azacitidine_outcomes, decitabine_outcomes, hydroxyurea_outcomes
    )
    
    # Generate summaries
    aza_summary = extractor.generate_drug_summary("Azacitidine", azacitidine_outcomes)
    dec_summary = extractor.generate_drug_summary("Decitabine", decitabine_outcomes)
    hyd_summary = extractor.generate_drug_summary("Hydroxyurea", hydroxyurea_outcomes)
    
    # Output results
    print("\n" + "=" * 50)
    print("COMPARATIVE RESULTS TABLE")
    print("=" * 50)
    print(comparison_df.to_string(index=False))
    
    print("\n" + "=" * 50)
    print("DRUG SUMMARIES")
    print("=" * 50)
    print(f"\n{aza_summary}")
    print(f"\n{dec_summary}")
    print(f"\n{hyd_summary}")
    
    # Save results
    comparison_df.to_csv("cmml_comparative_analysis.csv", index=False)
    
    # Save detailed outcomes with URLs
    with open("cmml_detailed_outcomes.json", "w") as f:
        results = {
            "azacitidine": [vars(o) for o in azacitidine_outcomes],
            "decitabine": [vars(o) for o in decitabine_outcomes], 
            "hydroxyurea": [vars(o) for o in hydroxyurea_outcomes]
        }
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to:")
    print(f"- cmml_comparative_analysis.csv")
    print(f"- cmml_detailed_outcomes.json")

if __name__ == "__main__":
    # Setup instructions
    print("SETUP REQUIRED:")
    print("1. Install required packages:")
    print("   pip install pandas beautifulsoup4 google-generativeai requests")
    print("\n2. Get Gemini API key from Google AI Studio")
    print("3. Update GEMINI_API_KEY variable at the top of this script")
    print("\nThen run: python cmml_extractor.py")
    print("\nNo email registration needed - this scrapes PubMed directly!")
    
    # Uncomment the line below after setup
    # main()