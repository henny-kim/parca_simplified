#!/usr/bin/env python3
"""
Clinical Outcomes Data Extractor for CMML Drugs
Uses PubMed API and AI to extract structured clinical data
"""

import requests
import json
import pandas as pd
from datetime import datetime
import time
from typing import Dict, List, Optional
import re

class ClinicalDataExtractor:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.api_key = None  # Add your API key here if you have one
        self.delay = 0.34  # Respect NCBI rate limits
        
    def search_pubmed(self, query: str, max_results: int = 50) -> List[str]:
        """Search PubMed and return PMIDs"""
        params = {
            'db': 'pubmed',
            'term': query,
            'retmode': 'json',
            'retmax': max_results,
            'sort': 'date'
        }
        if self.api_key:
            params['api_key'] = self.api_key
            
        response = requests.get(f"{self.base_url}esearch.fcgi", params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('esearchresult', {}).get('idlist', [])
        return []
    
    def get_abstracts(self, pmids: List[str]) -> List[Dict]:
        """Fetch abstracts for given PMIDs"""
        if not pmids:
            return []
            
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'rettype': 'abstract',
            'retmode': 'text'
        }
        if self.api_key:
            params['api_key'] = self.api_key
            
        response = requests.get(f"{self.base_url}efetch.fcgi", params=params)
        if response.status_code == 200:
            return self._parse_abstracts(response.text)
        return []
    
    def _parse_abstracts(self, text: str) -> List[Dict]:
        """Parse PubMed abstract text into structured data"""
        abstracts = []
        current_abstract = {}
        lines = text.split('\n')
        
        for line in lines:
            if line.startswith('PMID:'):
                if current_abstract:
                    abstracts.append(current_abstract)
                current_abstract = {'pmid': line.split(':')[1].strip()}
            elif line.startswith('DOI:'):
                current_abstract['doi'] = line.split(':')[1].strip()
            elif line.startswith('Title:'):
                current_abstract['title'] = line.split(':', 1)[1].strip()
            elif line.startswith('Author information:'):
                current_abstract['authors'] = line.split(':', 1)[1].strip()
            elif line.startswith('ABSTRACT:'):
                current_abstract['abstract'] = line.split(':', 1)[1].strip()
            elif current_abstract.get('abstract') and line.strip():
                current_abstract['abstract'] += ' ' + line.strip()
                
        if current_abstract:
            abstracts.append(current_abstract)
            
        return abstracts
    
    def extract_clinical_data(self, abstracts: List[Dict]) -> Dict:
        """Use AI-like pattern matching to extract clinical data"""
        clinical_data = {
            'azacitidine': {
                'response_rates': [],
                'survival_data': [],
                'adverse_events': [],
                'studies': []
            }
        }
        
        for abstract in abstracts:
            if not abstract.get('abstract'):
                continue
                
            text = abstract['abstract'].lower()
            
            # Extract response rates
            response_patterns = [
                r'overall response rate.*?(\d+(?:\.\d+)?)\s*%',
                r'orr.*?(\d+(?:\.\d+)?)\s*%',
                r'complete response.*?(\d+(?:\.\d+)?)\s*%',
                r'cr.*?(\d+(?:\.\d+)?)\s*%',
                r'partial response.*?(\d+(?:\.\d+)?)\s*%',
                r'pr.*?(\d+(?:\.\d+)?)\s*%'
            ]
            
            for pattern in response_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    clinical_data['azacitidine']['response_rates'].append({
                        'value': float(match),
                        'type': pattern.split('.*?')[0],
                        'pmid': abstract.get('pmid'),
                        'source': abstract.get('title', 'Unknown')
                    })
            
            # Extract survival data
            survival_patterns = [
                r'median overall survival.*?(\d+(?:\.\d+)?)\s*months',
                r'median os.*?(\d+(?:\.\d+)?)\s*months',
                r'median progression-free survival.*?(\d+(?:\.\d+)?)\s*months',
                r'median pfs.*?(\d+(?:\.\d+)?)\s*months'
            ]
            
            for pattern in survival_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    clinical_data['azacitidine']['survival_data'].append({
                        'value': float(match),
                        'type': pattern.split('.*?')[0],
                        'pmid': abstract.get('pmid'),
                        'source': abstract.get('title', 'Unknown')
                    })
            
            # Extract adverse events
            ae_patterns = [
                r'grade 3-4.*?(\d+(?:\.\d+)?)\s*%',
                r'neutropenia.*?(\d+(?:\.\d+)?)\s*%',
                r'thrombocytopenia.*?(\d+(?:\.\d+)?)\s*%',
                r'febrile neutropenia.*?(\d+(?:\.\d+)?)\s*%'
            ]
            
            for pattern in ae_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    clinical_data['azacitidine']['adverse_events'].append({
                        'value': float(match),
                        'type': pattern.split('.*?')[0],
                        'pmid': abstract.get('pmid'),
                        'source': abstract.get('title', 'Unknown')
                    })
            
            # Store study information
            if 'azacitidine' in text and ('cmml' in text or 'chronic myelomonocytic' in text):
                clinical_data['azacitidine']['studies'].append({
                    'pmid': abstract.get('pmid'),
                    'title': abstract.get('title', 'Unknown'),
                    'doi': abstract.get('doi', 'Unknown'),
                    'year': self._extract_year(abstract.get('title', ''))
                })
        
        return clinical_data
    
    def _extract_year(self, title: str) -> Optional[int]:
        """Extract year from title or return None"""
        year_match = re.search(r'20\d{2}', title)
        return int(year_match.group()) if year_match else None
    
    def generate_report(self, clinical_data: Dict) -> str:
        """Generate a structured report from extracted data"""
        report = "# Azacitidine Clinical Outcomes in CMML\n\n"
        
        az_data = clinical_data['azacitidine']
        
        # Response rates summary
        if az_data['response_rates']:
            report += "## Response Rates\n\n"
            response_types = {}
            for item in az_data['response_rates']:
                response_type = item['type']
                if response_type not in response_types:
                    response_types[response_type] = []
                response_types[response_type].append(item['value'])
            
            for response_type, values in response_types.items():
                avg_value = sum(values) / len(values)
                report += f"- **{response_type.title()}**: {avg_value:.1f}% (range: {min(values):.1f}-{max(values):.1f}%)\n"
            report += "\n"
        
        # Survival data summary
        if az_data['survival_data']:
            report += "## Survival Outcomes\n\n"
            survival_types = {}
            for item in az_data['survival_data']:
                survival_type = item['type']
                if survival_type not in survival_types:
                    survival_types[survival_type] = []
                survival_types[survival_type].append(item['value'])
            
            for survival_type, values in survival_types.items():
                avg_value = sum(values) / len(values)
                report += f"- **{survival_type.title()}**: {avg_value:.1f} months (range: {min(values):.1f}-{max(values):.1f} months)\n"
            report += "\n"
        
        # Adverse events summary
        if az_data['adverse_events']:
            report += "## Adverse Events\n\n"
            ae_types = {}
            for item in az_data['adverse_events']:
                ae_type = item['type']
                if ae_type not in ae_types:
                    ae_types[ae_type] = []
                ae_types[ae_type].append(item['value'])
            
            for ae_type, values in ae_types.items():
                avg_value = sum(values) / len(values)
                report += f"- **{ae_type.title()}**: {avg_value:.1f}% (range: {min(values):.1f}-{max(values):.1f}%)\n"
            report += "\n"
        
        # Studies summary
        if az_data['studies']:
            report += "## Key Studies\n\n"
            for study in az_data['studies'][:10]:  # Top 10 studies
                report += f"- **PMID {study['pmid']}**: {study['title']}\n"
                if study['doi'] != 'Unknown':
                    report += f"  - DOI: {study['doi']}\n"
                if study['year']:
                    report += f"  - Year: {study['year']}\n"
                report += "\n"
        
        return report

def main():
    """Main function to run the clinical data extraction"""
    extractor = ClinicalDataExtractor()
    
    # Search queries for azacitidine in CMML
    queries = [
        "azacitidine CMML clinical trial",
        "azacitidine chronic myelomonocytic leukemia response",
        "azacitidine CMML survival outcomes",
        "azacitidine CMML adverse events"
    ]
    
    all_pmids = set()
    for query in queries:
        print(f"Searching for: {query}")
        pmids = extractor.search_pubmed(query, max_results=20)
        all_pmids.update(pmids)
        time.sleep(extractor.delay)
    
    print(f"Found {len(all_pmids)} unique PMIDs")
    
    # Get abstracts
    print("Fetching abstracts...")
    abstracts = extractor.get_abstracts(list(all_pmids))
    print(f"Retrieved {len(abstracts)} abstracts")
    
    # Extract clinical data
    print("Extracting clinical data...")
    clinical_data = extractor.extract_clinical_data(abstracts)
    
    # Generate report
    print("Generating report...")
    report = extractor.generate_report(clinical_data)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with open(f"azacitidine_cmml_report_{timestamp}.md", "w") as f:
        f.write(report)
    
    # Save raw data as JSON
    with open(f"clinical_data_{timestamp}.json", "w") as f:
        json.dump(clinical_data, f, indent=2)
    
    print(f"Report saved as: azacitidine_cmml_report_{timestamp}.md")
    print(f"Raw data saved as: clinical_data_{timestamp}.json")
    
    # Print summary
    az_data = clinical_data['azacitidine']
    print(f"\nSummary:")
    print(f"- Response rates found: {len(az_data['response_rates'])}")
    print(f"- Survival data points: {len(az_data['survival_data'])}")
    print(f"- Adverse events: {len(az_data['adverse_events'])}")
    print(f"- Studies identified: {len(az_data['studies'])}")

if __name__ == "__main__":
    main() 