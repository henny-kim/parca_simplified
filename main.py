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
import xml.etree.ElementTree as ET
import argparse

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

@dataclass
class ClinicalOutcome:
    """Structure for CMML clinical outcome data with detailed efficacy measures"""
    # Core efficacy measures
    complete_response: Optional[float] = None
    partial_response: Optional[float] = None
    marrow_complete_response: Optional[float] = None
    marrow_optimal_response: Optional[float] = None
    pfs_median: Optional[float] = None
    os_median: Optional[float] = None
    efs_median: Optional[float] = None
    sae_frequency: Optional[float] = None
    
    # RAS mutation-specific data
    ras_mutant_data: Optional[Dict] = None
    non_ras_mutant_data: Optional[Dict] = None
    
    # Study metadata
    citation: str = ""
    pmid: str = ""
    url: str = ""
    cmml_sample_size: Optional[int] = None
    ras_mutant_sample_size: Optional[int] = None
    non_ras_mutant_sample_size: Optional[int] = None
    
    # Attribution fields
    key_findings: str = ""
    study_design: str = ""
    patient_population: str = ""
    treatment_details: str = ""
    supporting_quotes: List[str] = None
    data_source_location: str = ""

class PubMedScraper:
    """Enhanced PubMed scraper with multiple fallback methods"""
    
    def __init__(self):
        self.base_url = "https://pubmed.ncbi.nlm.nih.gov"
        self.eutils_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def fetch_pmc_fulltext(self, pmcid: str) -> Optional[str]:
        """Try to fetch full text from PMC via E-utilities (XML) and fallback to HTML scraping."""
        if not pmcid:
            return None
        # Normalize, accept forms like 'PMC1234567' or just the digits
        pmc_id_value = pmcid.replace('PMC', '')
        try:
            # Try efetch for PMC NXML
            fetch_url = f"{self.eutils_base}/efetch.fcgi"
            params = {
                'db': 'pmc',
                'id': pmc_id_value,
                'retmode': 'xml'
            }
            response = self.session.get(fetch_url, params=params)
            response.raise_for_status()
            try:
                root = ET.fromstring(response.content)
                body = root.find('.//body')
                if body is not None:
                    text = ''.join(body.itertext())
                    return re.sub(r'\s+', ' ', text).strip()[:200000]  # cap to 200k chars
            except ET.ParseError:
                pass
        except Exception:
            pass
        # Fallback to HTML scraping
        try:
            url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id_value}/"
            resp = self.session.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'html.parser')
            article = soup.select_one('div#maincontent') or soup
            text = article.get_text(separator=' ', strip=True)
            return re.sub(r'\s+', ' ', text).strip()[:200000]
        except Exception:
            return None

    def search_with_eutils(self, query: str, max_results: int = 20) -> List[str]:
        """Use E-utilities API to search for PMIDs (no API key required for basic searches)"""
        try:
            search_url = f"{self.eutils_base}/esearch.fcgi"
            params = {
                'db': 'pubmed',
                'term': query,
                'retmax': max_results,
                'retmode': 'json',
                'sort': 'relevance'
            }
            
            print(f"Searching E-utilities: {query}")
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            pmids = data.get('esearchresult', {}).get('idlist', [])
            print(f"Found {len(pmids)} PMIDs")
            return pmids
            
        except Exception as e:
            print(f"E-utilities search failed: {e}")
            return []

    def get_paper_details_eutils(self, pmids: List[str]) -> List[Dict]:
        """Get paper details using E-utilities (batched efetch across all PMIDs)."""
        if not pmids:
            return []
        try:
            fetch_url = f"{self.eutils_base}/efetch.fcgi"
            papers: List[Dict] = []
            # Batch efetch to avoid query length limits; PubMed supports large batches but be conservative
            batch_size = 100
            for i in range(0, len(pmids), batch_size):
                batch_ids = pmids[i:i+batch_size]
                params = {
                    'db': 'pubmed',
                    'id': ','.join(batch_ids),
                    'retmode': 'xml'
                }
                response = self.session.get(fetch_url, params=params)
                response.raise_for_status()
                root = ET.fromstring(response.content)
                for article in root.findall('.//PubmedArticle'):
                    try:
                        pmid_elem = article.find('.//PMID')
                        pmid = pmid_elem.text if pmid_elem is not None else None
                        title_elem = article.find('.//ArticleTitle')
                        title = title_elem.text if title_elem is not None else "No title"
                        # Abstract
                        abstract_parts = []
                        for abstract_elem in article.findall('.//AbstractText'):
                            label = abstract_elem.get('Label', '')
                            text = abstract_elem.text or ''
                            if label:
                                abstract_parts.append(f"{label}: {text}")
                            else:
                                abstract_parts.append(text)
                        abstract = " ".join(abstract_parts)
                        # Authors
                        authors = []
                        for author in article.findall('.//Author'):
                            last_name = author.find('.//LastName')
                            first_name = author.find('.//ForeName')
                            if last_name is not None:
                                author_name = last_name.text
                                if first_name is not None:
                                    author_name += f" {first_name.text}"
                                authors.append(author_name)
                        author_str = ", ".join(authors[:3])
                        if len(authors) > 3:
                            author_str += " et al."
                        # Journal/year
                        journal_elem = article.find('.//Journal/Title')
                        journal = journal_elem.text if journal_elem is not None else "Unknown journal"
                        year_elem = article.find('.//PubDate/Year')
                        year = year_elem.text if year_elem is not None else "Unknown year"
                        # Try to get PMCID for potential full text
                        pmcid_elem = article.find(".//ArticleIdList/ArticleId[@IdType='pmc']")
                        pmcid = pmcid_elem.text if pmcid_elem is not None else None
                        if pmid and title and abstract:
                            papers.append({
                                'pmid': pmid,
                                'title': title,
                                'abstract': abstract,
                                'authors': author_str,
                                'journal_info': f"{journal} ({year})",
                                'year': year,
                                'url': f"{self.base_url}/{pmid}/",
                                'pmcid': pmcid,
                                'full_content': f"Title: {title}\n\nAuthors: {author_str}\n\nJournal: {journal} ({year})\n\nAbstract: {abstract}"
                            })
                    except Exception as e:
                        print(f"Error parsing article: {e}")
                        continue
                time.sleep(0.34)  # ~3 req/sec respectful pacing
            return papers
        except Exception as e:
            print(f"Error fetching paper details: {e}")
            return []

    def search_pubmed_advanced(self, query: str, max_results: int = 20) -> List[Dict]:
        """Enhanced search method using multiple approaches"""
        print(f"Searching for: {query}")
        
        # Try E-utilities first
        pmids = self.search_with_eutils(query, max_results)
        if pmids:
            papers = self.get_paper_details_eutils(pmids)
            if papers:
                return papers
        
        # Fallback to web scraping with updated selectors
        return self.search_pubmed_web_fallback(query, max_results)

    def search_pubmed_web_fallback(self, query: str, max_results: int = 20) -> List[Dict]:
        """Fallback web scraping method with updated CSS selectors"""
        try:
            encoded_query = quote(query)
            search_url = f"{self.base_url}/?term={encoded_query}&size={max_results}"
            
            print(f"Trying web scraping: {search_url}")
            response = self.session.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple possible selectors for articles
            article_selectors = [
                'article.full-docsum',
                'div.docsum-wrap',
                'div.rprt',
                '[data-ga-action="result_click"]'
            ]
            
            articles = []
            for selector in article_selectors:
                articles = soup.select(selector)
                if articles:
                    print(f"Found articles using selector: {selector}")
                    break
            
            if not articles:
                print("No articles found with any selector")
                return []
            
            papers = []
            for article in articles[:max_results]:
                try:
                    # Try multiple methods to extract PMID
                    pmid = None
                    pmid_selectors = [
                        'strong.current-id',
                        '.docsum-pmid',
                        '[data-article-id]'
                    ]
                    
                    for selector in pmid_selectors:
                        pmid_elem = article.select_one(selector)
                        if pmid_elem:
                            pmid = pmid_elem.get_text(strip=True) or pmid_elem.get('data-article-id')
                            if pmid:
                                break
                    
                    # Try multiple methods to extract title
                    title = None
                    title_selectors = [
                        'a.docsum-title',
                        '.docsum-title a',
                        'h3 a'
                    ]
                    
                    for selector in title_selectors:
                        title_elem = article.select_one(selector)
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            if title:
                                break
                    
                    if pmid and title:
                        papers.append({
                            'pmid': pmid,
                            'title': title,
                            'authors': 'Unknown authors',
                            'journal_info': 'Unknown journal',
                            'snippet': '',
                            'url': f"{self.base_url}/{pmid}/"
                        })
                        
                except Exception as e:
                    print(f"Error parsing article: {e}")
                    continue
            
            print(f"Found {len(papers)} papers via web scraping")
            return papers
            
        except Exception as e:
            print(f"Web scraping fallback failed: {e}")
            return []

class CMMLResearchExtractor:
    def __init__(self, gemini_api_key: str, use_llm: bool = True):
        """Initialize the CMML research data extractor"""
        self.use_llm = use_llm and bool(gemini_api_key)
        self.model = None
        self.scraper = PubMedScraper()
        
        if self.use_llm:
            genai.configure(api_key=gemini_api_key)
        
        # Try different model names in order of preference
        if self.use_llm:
            model_names = [
                'gemini-1.5-flash',
                'gemini-1.5-pro', 
                'gemini-pro',
                'models/gemini-1.5-flash',
                'models/gemini-1.5-pro',
                'models/gemini-pro'
            ]
            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    print(f"Successfully initialized model: {model_name}")
                    break
                except Exception as e:
                    print(f"Failed to initialize {model_name}: {e}")
                    continue
            if not self.model:
                print("Warning: Could not initialize any Gemini model. Falling back to regex-based extraction.")
                self.use_llm = False
        
        # Enhanced extraction prompt template focused on specific efficacy measures
        self.extraction_prompt = """
        You are a medical research data extraction specialist. Extract CMML-specific clinical outcomes from this research paper.

        Paper content: {paper_content}

        Extract ONLY data specifically for CMML (chronic myelomonocytic leukemia). 
        EXCLUDE any general MDS (myelodysplastic syndrome) or MPS/MPD (myeloproliferative syndrome/disorder) data unless it is explicitly broken down for CMML patients only.

        Focus on these specific efficacy measures:
        - Complete Response (CR)
        - Partial Response (PR) 
        - Marrow Complete Response (mCR)
        - Marrow Optimal Response (mOR)
        - Progression Free Survival (PFS)
        - Overall Survival (OS)
        - Event Free Survival (EFS)
        - Serious Adverse Events (SAEs)

        If data is available by RAS mutation status, extract both RAS-mutant and non-RAS-mutant outcomes separately.

        Return the data in this exact JSON format:
        {{
            "drug_name": "string (azacitidine, decitabine, or hydroxyurea)",
            "complete_response_rate": number or null,
            "partial_response_rate": number or null, 
            "marrow_complete_response_rate": number or null,
            "marrow_optimal_response_rate": number or null,
            "pfs_median_months": number or null,
            "os_median_months": number or null,
            "efs_median_months": number or null,
            "sae_frequency_percent": number or null,
            "ras_mutant_outcomes": {{
                "cr_rate": number or null,
                "pr_rate": number or null,
                "mcr_rate": number or null,
                "mor_rate": number or null,
                "os_median": number or null,
                "pfs_median": number or null,
                "efs_median": number or null,
                "sae_rate": number or null
            }},
            "non_ras_mutant_outcomes": {{
                "cr_rate": number or null,
                "pr_rate": number or null,
                "mcr_rate": number or null,
                "mor_rate": number or null,
                "os_median": number or null,
                "pfs_median": number or null,
                "efs_median": number or null,
                "sae_rate": number or null
            }},
            "cmml_sample_size": number or null,
            "ras_mutant_sample_size": number or null,
            "non_ras_mutant_sample_size": number or null,
            "study_type": "string",
            "has_cmml_data": true or false,
            "key_findings": "string - brief summary of main CMML findings",
            "patient_population": "string - describe the CMML patient cohort",
            "treatment_details": "string - dosing, schedule, combination details",
            "supporting_quotes": ["array of direct quotes from paper supporting the extracted numbers"],
            "data_location": "string - where in the paper this data was found"
        }}

        CRITICAL RULES:
        - Return percentages as numbers (e.g., 25.5 for 25.5%)
        - Return survival times in months only
        - Only extract data explicitly stated for CMML patients
        - If a study includes MDS and CMML mixed, only extract if CMML results are reported separately
        - Set has_cmml_data to true ONLY if the paper contains specific CMML outcome data
        - Include direct quotes that support your extracted numbers
        - If RAS mutation status is not reported, set those fields to null
        - Be conservative - if unclear, set to null rather than guess
        """

    def extract_clinical_data(self, paper_content: str) -> Optional[Dict]:
        """Extract clinical data from paper content using LLM or regex fallback"""
        if not self.use_llm or not self.model:
            return self.extract_with_regex(paper_content)
        try:
            prompt = self.extraction_prompt.format(paper_content=paper_content)
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=2048
            )
            response = self.model.generate_content(prompt, generation_config=generation_config)
            if not response.text:
                print("Empty response from Gemini; falling back to regex")
                return self.extract_with_regex(paper_content)
            json_start = response.text.find('{')
            json_end = response.text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response.text[json_start:json_end]
                try:
                    data = json.loads(json_str)
                except json.JSONDecodeError as json_error:
                    print(f"JSON decode error: {json_error}")
                    print(f"Raw response: {response.text[:500]}...")
                    return self.extract_with_regex(paper_content)
                if not data.get('has_cmml_data', False):
                    return None
                return data
            else:
                print("No valid JSON found in response; falling back to regex")
                return self.extract_with_regex(paper_content)
        except Exception as e:
            print(f"Error extracting data with Gemini: {e}")
            return self.extract_with_regex(paper_content)

    def extract_with_regex(self, paper_content: str) -> Optional[Dict]:
        text = paper_content
        lower = text.lower()
        if 'cmml' not in lower and 'chronic myelomonocytic leukemia' not in lower:
            return None
        def find_pct(patterns):
            for rx in patterns:
                m = re.search(rx, text, flags=re.IGNORECASE)
                if m:
                    try:
                        return float(m.group(1))
                    except Exception:
                        continue
            return None
        def find_months(patterns):
            for rx in patterns:
                m = re.search(rx, text, flags=re.IGNORECASE)
                if m:
                    try:
                        return float(m.group(1))
                    except Exception:
                        continue
            return None
        cr = find_pct([
            r"\bcomplete\s+response[^\d%]*([0-9]+(?:\.[0-9]+)?)%",
            r"\bCR\b[^\d%]*([0-9]+(?:\.[0-9]+)?)%",
            r"([0-9]+(?:\.[0-9]+)?)%[^\n\r]*\b(complete\s+response|CR)\b"
        ])
        pr = find_pct([
            r"\bpartial\s+response[^\d%]*([0-9]+(?:\.[0-9]+)?)%",
            r"\bPR\b[^\d%]*([0-9]+(?:\.[0-9]+)?)%",
            r"([0-9]+(?:\.[0-9]+)?)%[^\n\r]*\b(partial\s+response|PR)\b"
        ])
        mcr = find_pct([
            r"\bmarrow\s+complete\s+response[^\d%]*([0-9]+(?:\.[0-9]+)?)%",
            r"\bmCR\b[^\d%]*([0-9]+(?:\.[0-9]+)?)%"
        ])
        mor = find_pct([
            r"\bmarrow\s+optimal\s+response[^\d%]*([0-9]+(?:\.[0-9]+)?)%",
            r"\bmOR\b[^\d%]*([0-9]+(?:\.[0-9]+)?)%"
        ])
        orr = find_pct([
            r"overall\s+response\s+rate[^\d%]*([0-9]+(?:\.[0-9]+)?)%",
            r"\bORR\b[^\d%]*([0-9]+(?:\.[0-9]+)?)%",
            r"([0-9]+(?:\.[0-9]+)?)%[^\n\r]*overall\s+response\s+rate"
        ])
        os_m = find_months([
            r"median\s+overall\s+survival[^\d]*([0-9]+(?:\.[0-9]+)?)\s*months",
            r"\bOS\b[^\d]*([0-9]+(?:\.[0-9]+)?)\s*months"
        ])
        pfs_m = find_months([
            r"median\s+progression[- ]free\s+survival[^\d]*([0-9]+(?:\.[0-9]+)?)\s*months",
            r"\bPFS\b[^\d]*([0-9]+(?:\.[0-9]+)?)\s*months"
        ])
        efs_m = find_months([
            r"median\s+event[- ]free\s+survival[^\d]*([0-9]+(?:\.[0-9]+)?)\s*months",
            r"\bEFS\b[^\d]*([0-9]+(?:\.[0-9]+)?)\s*months"
        ])
        sae = find_pct([
            r"serious\s+adverse\s+events?[^\d%]*([0-9]+(?:\.[0-9]+)?)%",
            r"\bSAEs?\b[^\d%]*([0-9]+(?:\.[0-9]+)?)%"
        ])
        # Minimal payload matching the LLM output keys used downstream
        has_any = any(v is not None for v in [cr, pr, mcr, mor, os_m, pfs_m, efs_m, sae, orr])
        if not has_any:
            return None
        return {
            'drug_name': '',
            'complete_response_rate': cr,
            'partial_response_rate': pr,
            'marrow_complete_response_rate': mcr,
            'marrow_optimal_response_rate': mor,
            'pfs_median_months': pfs_m,
            'os_median_months': os_m,
            'efs_median_months': efs_m,
            'sae_frequency_percent': sae,
            'ras_mutant_outcomes': {
                'cr_rate': None, 'pr_rate': None, 'mcr_rate': None, 'mor_rate': None,
                'os_median': None, 'pfs_median': None, 'efs_median': None, 'sae_rate': None
            },
            'non_ras_mutant_outcomes': {
                'cr_rate': None, 'pr_rate': None, 'mcr_rate': None, 'mor_rate': None,
                'os_median': None, 'pfs_median': None, 'efs_median': None, 'sae_rate': None
            },
            'cmml_sample_size': None,
            'ras_mutant_sample_size': None,
            'non_ras_mutant_sample_size': None,
            'study_type': '',
            'has_cmml_data': True,
            'key_findings': '',
            'patient_population': '',
            'treatment_details': '',
            'supporting_quotes': [],
            'data_location': 'Abstract'
        }

    def process_drug_research(self, drug_name: str, additional_terms: str = "", max_results: int = 20, per_paper_sleep: float = 0.0) -> List[ClinicalOutcome]:
        """Process all research for a specific drug with improved search queries"""
        print(f"\n=== Processing {drug_name} research ===")
        
        # Improved search queries
        queries = [
            f"{drug_name} CMML",
            f"{drug_name} chronic myelomonocytic leukemia",
            f"CMML {drug_name} treatment",
            f"chronic myelomonocytic leukemia {drug_name}",
            f"{drug_name} myelodysplastic syndrome CMML"
        ]
        
        if additional_terms:
            queries.append(f"CMML {additional_terms} {drug_name}")
        
        all_papers = []
        seen_pmids = set()
        
        for query in queries:
            papers = self.scraper.search_pubmed_advanced(query, max_results=max_results)
            
            # Deduplicate by PMID
            for paper in papers:
                if paper['pmid'] not in seen_pmids:
                    all_papers.append(paper)
                    seen_pmids.add(paper['pmid'])
            
            time.sleep(2)  # Rate limiting
        
        print(f"Total unique papers found: {len(all_papers)}")
        
        if not all_papers:
            print("No papers found. This might be due to:")
            print("1. PubMed blocking automated requests")
            print("2. Changes in PubMed's interface")
            print("3. Very specific search terms with limited results")
            return []
        
        clinical_outcomes = []
        
        for i, paper in enumerate(all_papers[:min(len(all_papers), max_results)]):
            print(f"Processing paper {i+1}/{min(len(all_papers), 15)}: {paper['title'][:60]}...")
            
            # Relevance check: if LLM enabled, let AI decide; else use keyword filter
            keyword_relevant = ('cmml' in f"{paper['title']} {paper.get('abstract', '')} {paper.get('snippet', '')}".lower() or 
                                 'chronic myelomonocytic leukemia' in f"{paper['title']} {paper.get('abstract', '')} {paper.get('snippet', '')}".lower())
            
            # If we have abstract from E-utilities, use it directly; otherwise fetch
            if paper.get('abstract'):
                paper_data = paper
            else:
                full_paper = self.scraper.get_paper_details_eutils([paper['pmid']])
                paper_data = full_paper[0] if full_paper else paper
            
            if not paper_data.get('abstract') and not paper_data.get('snippet'):
                print(f"  Skipping - no abstract available")
                continue
            
            # Build content: prefer PMC full text when LLM is on, else abstract
            content = paper_data.get('full_content') or f"Title: {paper_data['title']}\n\nAbstract: {paper_data.get('abstract', paper_data.get('snippet', ''))}"
            if self.use_llm and paper_data.get('pmcid'):
                pmc_text = self.scraper.fetch_pmc_fulltext(paper_data['pmcid'])
                if pmc_text:
                    content = f"Title: {paper_data['title']}\n\nFullText: {pmc_text}"
            # If LLM disabled, require keyword relevance; if enabled, rely on model
            if not self.use_llm and not keyword_relevant:
                print("  Skipping - not CMML relevant (keyword filter)")
                continue
            extracted_data = self.extract_clinical_data(content)
            
            if not extracted_data:
                print(f"  No CMML-specific data found")
                continue
            
            # Convert to ClinicalOutcome object with enhanced efficacy measures
            outcome = ClinicalOutcome(
                complete_response=extracted_data.get('complete_response_rate'),
                partial_response=extracted_data.get('partial_response_rate'),
                marrow_complete_response=extracted_data.get('marrow_complete_response_rate'),
                marrow_optimal_response=extracted_data.get('marrow_optimal_response_rate'),
                pfs_median=extracted_data.get('pfs_median_months'),
                os_median=extracted_data.get('os_median_months'),
                efs_median=extracted_data.get('efs_median_months'),
                sae_frequency=extracted_data.get('sae_frequency_percent'),
                ras_mutant_data=extracted_data.get('ras_mutant_outcomes'),
                non_ras_mutant_data=extracted_data.get('non_ras_mutant_outcomes'),
                citation=f"{paper_data.get('authors', 'Unknown')} {paper_data['title']} {paper_data.get('journal_info', 'Unknown journal')}",
                pmid=paper_data['pmid'],
                url=paper_data['url'],
                # Sample sizes
                cmml_sample_size=extracted_data.get('cmml_sample_size'),
                ras_mutant_sample_size=extracted_data.get('ras_mutant_sample_size'),
                non_ras_mutant_sample_size=extracted_data.get('non_ras_mutant_sample_size'),
                # Attribution fields
                key_findings=extracted_data.get('key_findings', ''),
                study_design=extracted_data.get('study_type', ''),
                patient_population=extracted_data.get('patient_population', ''),
                treatment_details=extracted_data.get('treatment_details', ''),
                supporting_quotes=extracted_data.get('supporting_quotes', []),
                data_source_location=extracted_data.get('data_location', '')
            )
            
            clinical_outcomes.append(outcome)
            print(f"  ✓ Extracted CMML data")
            
            if per_paper_sleep > 0:
                time.sleep(per_paper_sleep)
        
        return clinical_outcomes

    def create_comparative_table(self, azacitidine_data: List[ClinicalOutcome], 
                                decitabine_data: List[ClinicalOutcome],
                                hydroxyurea_data: List[ClinicalOutcome]) -> pd.DataFrame:
        """Create the comparative efficacy table focused on specific measures"""
        
        def aggregate_outcomes(outcomes: List[ClinicalOutcome], drug_name: str):
            """Aggregate outcomes for a drug, combining data from multiple studies"""
            if not outcomes:
                return {
                    'Drug': drug_name,
                    'CMML Subtype': 'Overall',
                    'Complete Response (%)': '...',
                    'Partial Response (%)': '...',
                    'Marrow CR (%)': '...',
                    'Marrow Optimal (%)': '...',
                    'PFS (months)': '...',
                    'OS (months)': '...',
                    'EFS (months)': '...',
                    'SAEs (%)': '...',
                    'Sample Size': '...'
                }
            
            # Find best available data for each metric
            cr_rates = [o.complete_response for o in outcomes if o.complete_response is not None]
            pr_rates = [o.partial_response for o in outcomes if o.partial_response is not None]
            mcr_rates = [o.marrow_complete_response for o in outcomes if o.marrow_complete_response is not None]
            mor_rates = [o.marrow_optimal_response for o in outcomes if o.marrow_optimal_response is not None]
            pfs_values = [o.pfs_median for o in outcomes if o.pfs_median is not None]
            os_values = [o.os_median for o in outcomes if o.os_median is not None]
            efs_values = [o.efs_median for o in outcomes if o.efs_median is not None]
            sae_rates = [o.sae_frequency for o in outcomes if o.sae_frequency is not None]
            sample_sizes = [o.cmml_sample_size for o in outcomes if o.cmml_sample_size is not None]
            
            total_sample = sum(sample_sizes) if sample_sizes else None
            
            return {
                'Drug': drug_name,
                'CMML Subtype': 'Overall',
                'Complete Response (%)': f"{cr_rates[0]:.1f}" if cr_rates else '...',
                'Partial Response (%)': f"{pr_rates[0]:.1f}" if pr_rates else '...',
                'Marrow CR (%)': f"{mcr_rates[0]:.1f}" if mcr_rates else '...',
                'Marrow Optimal (%)': f"{mor_rates[0]:.1f}" if mor_rates else '...',
                'PFS (months)': f"{pfs_values[0]:.1f}" if pfs_values else '...',
                'OS (months)': f"{os_values[0]:.1f}" if os_values else '...',
                'EFS (months)': f"{efs_values[0]:.1f}" if efs_values else '...',
                'SAEs (%)': f"{sae_rates[0]:.1f}" if sae_rates else '...',
                'Sample Size': f"{total_sample}" if total_sample else '...'
            }
        
        def add_mutation_rows(outcomes: List[ClinicalOutcome], drug_name: str):
            """Add RAS mutation-specific rows if data is available"""
            rows = []
            
            # Check if any outcome has RAS mutation data
            has_ras_data = any(o.ras_mutant_data for o in outcomes if o.ras_mutant_data)
            has_non_ras_data = any(o.non_ras_mutant_data for o in outcomes if o.non_ras_mutant_data)
            
            if has_ras_data:
                ras_outcomes = [o for o in outcomes if o.ras_mutant_data]
                ras_data = ras_outcomes[0].ras_mutant_data
                ras_sample = ras_outcomes[0].ras_mutant_sample_size
                
                rows.append({
                    'Drug': '',
                    'CMML Subtype': 'RAS-mutant',
                    'Complete Response (%)': f"{ras_data.get('cr_rate', 0):.1f}" if ras_data.get('cr_rate') else '...',
                    'Partial Response (%)': f"{ras_data.get('pr_rate', 0):.1f}" if ras_data.get('pr_rate') else '...',
                    'Marrow CR (%)': f"{ras_data.get('mcr_rate', 0):.1f}" if ras_data.get('mcr_rate') else '...',
                    'Marrow Optimal (%)': f"{ras_data.get('mor_rate', 0):.1f}" if ras_data.get('mor_rate') else '...',
                    'PFS (months)': f"{ras_data.get('pfs_median', 0):.1f}" if ras_data.get('pfs_median') else '...',
                    'OS (months)': f"{ras_data.get('os_median', 0):.1f}" if ras_data.get('os_median') else '...',
                    'EFS (months)': f"{ras_data.get('efs_median', 0):.1f}" if ras_data.get('efs_median') else '...',
                    'SAEs (%)': f"{ras_data.get('sae_rate', 0):.1f}" if ras_data.get('sae_rate') else '...',
                    'Sample Size': f"{ras_sample}" if ras_sample else '...'
                })
            else:
                rows.append({
                    'Drug': '', 'CMML Subtype': 'RAS-mutant',
                    'Complete Response (%)': '...', 'Partial Response (%)': '...',
                    'Marrow CR (%)': '...', 'Marrow Optimal (%)': '...',
                    'PFS (months)': '...', 'OS (months)': '...',
                    'EFS (months)': '...', 'SAEs (%)': '...', 'Sample Size': '...'
                })
            
            if has_non_ras_data:
                non_ras_outcomes = [o for o in outcomes if o.non_ras_mutant_data]
                non_ras_data = non_ras_outcomes[0].non_ras_mutant_data
                non_ras_sample = non_ras_outcomes[0].non_ras_mutant_sample_size
                
                rows.append({
                    'Drug': '',
                    'CMML Subtype': 'Non-RAS-mutant',
                    'Complete Response (%)': f"{non_ras_data.get('cr_rate', 0):.1f}" if non_ras_data.get('cr_rate') else '...',
                    'Partial Response (%)': f"{non_ras_data.get('pr_rate', 0):.1f}" if non_ras_data.get('pr_rate') else '...',
                    'Marrow CR (%)': f"{non_ras_data.get('mcr_rate', 0):.1f}" if non_ras_data.get('mcr_rate') else '...',
                    'Marrow Optimal (%)': f"{non_ras_data.get('mor_rate', 0):.1f}" if non_ras_data.get('mor_rate') else '...',
                    'PFS (months)': f"{non_ras_data.get('pfs_median', 0):.1f}" if non_ras_data.get('pfs_median') else '...',
                    'OS (months)': f"{non_ras_data.get('os_median', 0):.1f}" if non_ras_data.get('os_median') else '...',
                    'EFS (months)': f"{non_ras_data.get('efs_median', 0):.1f}" if non_ras_data.get('efs_median') else '...',
                    'SAEs (%)': f"{non_ras_data.get('sae_rate', 0):.1f}" if non_ras_data.get('sae_rate') else '...',
                    'Sample Size': f"{non_ras_sample}" if non_ras_sample else '...'
                })
            else:
                rows.append({
                    'Drug': '', 'CMML Subtype': 'Non-RAS-mutant', 
                    'Complete Response (%)': '...', 'Partial Response (%)': '...',
                    'Marrow CR (%)': '...', 'Marrow Optimal (%)': '...',
                    'PFS (months)': '...', 'OS (months)': '...',
                    'EFS (months)': '...', 'SAEs (%)': '...', 'Sample Size': '...'
                })
            
            return rows
        
        # Create rows for the table
        rows = []
        
        # Process each drug
        for drug_name, outcomes in [("Azacitidine", azacitidine_data), 
                                   ("Decitabine", decitabine_data), 
                                   ("Hydroxyurea", hydroxyurea_data)]:
            rows.append(aggregate_outcomes(outcomes, drug_name))
            rows.extend(add_mutation_rows(outcomes, drug_name))
        
        return pd.DataFrame(rows)

    def generate_drug_summary(self, drug_name: str, outcomes: List[ClinicalOutcome]) -> str:
        """Generate a paragraph summary for each drug with detailed attribution"""
        if not outcomes:
            return f"{drug_name}: Limited CMML-specific data available in the literature."
        
        # Extract key findings
        response_rates = [o.complete_response for o in outcomes if o.complete_response is not None]
        survival_data = [o.os_median for o in outcomes if o.os_median is not None]
        safety_data = [o.sae_frequency for o in outcomes if o.sae_frequency is not None]
        
        # Get sample sizes for context
        sample_sizes = [o.cmml_sample_size for o in outcomes if o.cmml_sample_size is not None]
        total_patients = sum(sample_sizes) if sample_sizes else None
        
        # Top 3 citations with more detail
        top_studies = []
        for outcome in outcomes[:3]:
            study_detail = f"PMID:{outcome.pmid}"
            if outcome.cmml_sample_size:
                study_detail += f" (n={outcome.cmml_sample_size})"
            if outcome.data_source_location:
                study_detail += f" [{outcome.data_source_location}]"
            top_studies.append(study_detail)
        
        summary = f"{drug_name}: "
        if response_rates:
            summary += f"Shows clinical activity in CMML with complete response rates ranging from {min(response_rates):.1f}% to {max(response_rates):.1f}%. "
        if survival_data:
            summary += f"Median overall survival reported as {min(survival_data):.1f}-{max(survival_data):.1f} months. "
        if safety_data:
            summary += f"Safety profile shows {min(safety_data):.1f}-{max(safety_data):.1f}% serious adverse events. "
        
        if total_patients:
            summary += f"Data from {len(outcomes)} CMML-specific studies (total n={total_patients} patients). "
        else:
            summary += f"Based on {len(outcomes)} CMML-specific studies. "
            
        summary += f"Key studies: {', '.join(top_studies)}."
        
        return summary

def test_gemini_api(api_key: str):
    """Test Gemini API with a simple request"""
    try:
        genai.configure(api_key=api_key)
        
        # List available models
        models = genai.list_models()
        available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        print(f"Available models: {available_models}")
        
        if not available_models:
            print("No models available for content generation")
            return False
        
        # Test with a simple request
        model = genai.GenerativeModel(available_models[0])
        response = model.generate_content("Hello, respond with just 'OK'")
        print(f"Test response: {response.text}")
        return True
        
    except Exception as e:
        print(f"Gemini API test failed: {e}")
        return False

def main():
    """Main execution function with CLI controls"""
    parser = argparse.ArgumentParser(description="CMML data extractor")
    parser.add_argument("--drug", choices=["azacitidine", "decitabine", "hydroxyurea", "all"], default="all", help="Which drug to process")
    parser.add_argument("--max", type=int, default=30, help="Max number of search results/papers to process per query")
    parser.add_argument("--sleep", type=float, default=0.0, help="Seconds to sleep between processing papers (politeness)")
    parser.add_argument("--append", action="store_true", help="Append/update existing JSON instead of overwriting fully")
    args = parser.parse_args()

    # Check API key
    # If no API key, we will fall back to regex extraction automatically
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        print("GEMINI_API_KEY not set. Proceeding with regex-based extraction.")
        api_ok = False
    else:
        print("Testing Gemini API connection...")
        api_ok = test_gemini_api(GEMINI_API_KEY)
        if not api_ok:
            print("Gemini API test failed. Falling back to regex-based extraction.")

    # Initialize extractor
    try:
        extractor = CMMLResearchExtractor(gemini_api_key=GEMINI_API_KEY, use_llm=api_ok)
    except Exception as e:
        print(f"Failed to initialize extractor: {e}")
        return

    print("\nCMML Clinical Data Extraction Starting...")
    print("Enhanced version with E-utilities API and fallback methods")
    print("=" * 50)

    # Process selected drugs
    azacitidine_outcomes: List[ClinicalOutcome] = []
    decitabine_outcomes: List[ClinicalOutcome] = []
    hydroxyurea_outcomes: List[ClinicalOutcome] = []

    if args.drug in ("azacitidine", "all"):
        azacitidine_outcomes = extractor.process_drug_research("azacitidine", "hypomethylating", max_results=args.max, per_paper_sleep=args.sleep)
    if args.drug in ("decitabine", "all"):
        decitabine_outcomes = extractor.process_drug_research("decitabine", "hypomethylating", max_results=args.max, per_paper_sleep=args.sleep)
    if args.drug in ("hydroxyurea", "all"):
        hydroxyurea_outcomes = extractor.process_drug_research("hydroxyurea", "cytoreductive", max_results=args.max, per_paper_sleep=args.sleep)

    # Load existing JSON if append mode
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file_path = os.path.join(output_dir, "cmml_detailed_outcomes.json")
    existing = None
    if args.append and os.path.exists(output_file_path):
        try:
            with open(output_file_path, "r") as rf:
                existing = json.load(rf)
        except Exception:
            existing = None

    # Create comparative table if all drugs processed
    if args.drug == "all":
        comparison_df = extractor.create_comparative_table(
            azacitidine_outcomes, decitabine_outcomes, hydroxyurea_outcomes
        )
        print("\n" + "=" * 50)
        print("COMPARATIVE RESULTS TABLE")
        print("=" * 50)
        print(comparison_df.to_string(index=False))
        comparison_df.to_csv(os.path.join(output_dir, "cmml_comparative_analysis.csv"), index=False)

    # Build JSON payload
    print("\nSaving detailed results with attributions...")
    results = existing or {}
    if not existing:
        results = {
            "extraction_metadata": {
                "extraction_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_papers_processed": 0,
                "note": "All data includes direct quotes and source locations for verification"
            },
            "azacitidine": [],
            "decitabine": [],
            "hydroxyurea": []
        }

    # Helper to serialize outcomes
    def serialize(outcomes: List[ClinicalOutcome]):
        return [
            {
                **vars(o),
                "reference_note": f"See PMID {o.pmid} - {o.data_source_location}",
                "verification_url": o.url
            } for o in outcomes
        ]

    if args.drug in ("azacitidine", "all"):
        results["azacitidine"] = serialize(azacitidine_outcomes) if not args.append else (results.get("azacitidine", []) + serialize(azacitidine_outcomes))
    if args.drug in ("decitabine", "all"):
        results["decitabine"] = serialize(decitabine_outcomes) if not args.append else (results.get("decitabine", []) + serialize(decitabine_outcomes))
    if args.drug in ("hydroxyurea", "all"):
        results["hydroxyurea"] = serialize(hydroxyurea_outcomes) if not args.append else (results.get("hydroxyurea", []) + serialize(hydroxyurea_outcomes))

    # Update metadata
    total = len(results.get("azacitidine", [])) + len(results.get("decitabine", [])) + len(results.get("hydroxyurea", []))
    results["extraction_metadata"]["extraction_date"] = time.strftime("%Y-%m-%d %H:%M:%S")
    results["extraction_metadata"]["total_papers_processed"] = total

    with open(output_file_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Attribution file (optional)
    with open(os.path.join(output_dir, "cmml_attribution_summary.txt"), "w") as f:
        f.write("CMML CLINICAL DATA - ATTRIBUTION SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        for drug_name, outcomes in [("Azacitidine", [ClinicalOutcome(**{k: v for k, v in x.items() if k in ClinicalOutcome().__dict__.keys()}) for x in results.get("azacitidine", [])]),
                                   ("Decitabine", [ClinicalOutcome(**{k: v for k, v in x.items() if k in ClinicalOutcome().__dict__.keys()}) for x in results.get("decitabine", [])]),
                                   ("Hydroxyurea", [ClinicalOutcome(**{k: v for k, v in x.items() if k in ClinicalOutcome().__dict__.keys()}) for x in results.get("hydroxyurea", [])])]:
            f.write(f"{drug_name.upper()}\n")
            f.write("-" * len(drug_name) + "\n")
            for i, outcome in enumerate(outcomes, 1):
                f.write(f"\n{i}. PMID {outcome.pmid}\n")
                f.write(f"   Citation: {outcome.citation[:100]}...\n")
                if outcome.key_findings:
                    f.write(f"   Key Findings: {outcome.key_findings}\n")
                if outcome.patient_population:
                    f.write(f"   Patient Population: {outcome.patient_population}\n")
                if outcome.treatment_details:
                    f.write(f"   Treatment: {outcome.treatment_details}\n")
                if outcome.data_source_location:
                    f.write(f"   Data Location: {outcome.data_source_location}\n")
                if outcome.complete_response is not None:
                    f.write(f"   Complete Response: {outcome.complete_response}%\n")
                if outcome.partial_response is not None:
                    f.write(f"   Partial Response: {outcome.partial_response}%\n")
                if outcome.os_median is not None:
                    f.write(f"   Overall Survival: {outcome.os_median} months\n")
                if outcome.supporting_quotes:
                    f.write("   Supporting Quotes:\n")
                    for quote in outcome.supporting_quotes[:2]:
                        f.write(f"     - \"{str(quote)[:100]}...\"\n")
                f.write(f"   URL: {outcome.url}\n")
            f.write("\n" + "=" * 50 + "\n")

    print("\nSaved:")
    if args.drug == "all":
        print("- cmml_comparative_analysis.csv (summary table)")
    print("- cmml_detailed_outcomes.json (complete data with attributions)")
    print("- cmml_attribution_summary.txt (readable reference guide)")

if __name__ == "__main__":
    main()