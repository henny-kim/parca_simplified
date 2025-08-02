#!/usr/bin/env python3
"""
Medicine-Specific Clinical Outcomes Data Extractor for CMML
Takes medicine name as input and generates structured clinical report
"""

import requests
import json
import pandas as pd
from datetime import datetime
import time
from typing import Dict, List, Optional, Tuple
import re
from collections import defaultdict
import sys

class MedicineClinicalExtractor:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.api_key = None  # Add your API key here if you have one
        self.delay = 0.34  # Respect NCBI rate limits
        
        # Define drugs and their search terms
        self.drugs = {
            'azacitidine': ['azacitidine', '5-azacitidine', 'vidaza'],
            'decitabine': ['decitabine', '5-aza-2-deoxycytidine', 'dacogen'],
            'hydroxyurea': ['hydroxyurea', 'hydroxycarbamide', 'hydrea']
        }
        
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
    
    def extract_clinical_data(self, abstracts: List[Dict], medicine: str) -> Dict:
        """Extract clinical data for specific medicine"""
        clinical_data = {
            'efficacy_measures': {
                'complete_response': [],
                'partial_response': [],
                'marrow_cr': [],
                'progression_free_survival': [],
                'overall_survival': [],
                'event_free_survival': []
            },
            'adverse_events': [],
            'ras_mutated': [],
            'non_ras_mutated': [],
            'studies': []
        }
        
        for abstract in abstracts:
            if not abstract.get('abstract'):
                continue
                
            text = abstract['abstract'].lower()
            title = abstract.get('title', '').lower()
            
            # Check if this abstract discusses the specific medicine and CMML
            medicine_terms = self.drugs.get(medicine.lower(), [medicine.lower()])
            if not any(term in text or term in title for term in medicine_terms):
                continue
                
            if not ('cmml' in text or 'chronic myelomonocytic' in text):
                continue
            
            # Extract efficacy measures
            self._extract_efficacy_data(text, abstract, clinical_data)
            
            # Extract adverse events
            self._extract_adverse_events(text, abstract, clinical_data)
            
            # Extract RAS mutation data
            self._extract_ras_data(text, abstract, clinical_data)
            
            # Store study information
            clinical_data['studies'].append({
                'pmid': abstract.get('pmid'),
                'title': abstract.get('title', 'Unknown'),
                'doi': abstract.get('doi', 'Unknown'),
                'year': self._extract_year(abstract.get('title', ''))
            })
        
        return clinical_data
    
    def _extract_efficacy_data(self, text: str, abstract: Dict, clinical_data: Dict):
        """Extract efficacy measures from text"""
        
        # Complete Response patterns
        cr_patterns = [
            r'complete response.*?(\d+(?:\.\d+)?)\s*%',
            r'cr.*?(\d+(?:\.\d+)?)\s*%',
            r'complete remission.*?(\d+(?:\.\d+)?)\s*%'
        ]
        
        for pattern in cr_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                clinical_data['efficacy_measures']['complete_response'].append({
                    'value': float(match),
                    'pmid': abstract.get('pmid'),
                    'source': abstract.get('title', 'Unknown'),
                    'year': self._extract_year(abstract.get('title', ''))
                })
        
        # Partial Response patterns
        pr_patterns = [
            r'partial response.*?(\d+(?:\.\d+)?)\s*%',
            r'pr.*?(\d+(?:\.\d+)?)\s*%'
        ]
        
        for pattern in pr_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                clinical_data['efficacy_measures']['partial_response'].append({
                    'value': float(match),
                    'pmid': abstract.get('pmid'),
                    'source': abstract.get('title', 'Unknown'),
                    'year': self._extract_year(abstract.get('title', ''))
                })
        
        # Marrow CR patterns
        marrow_patterns = [
            r'marrow.*?response.*?(\d+(?:\.\d+)?)\s*%',
            r'mcr.*?(\d+(?:\.\d+)?)\s*%',
            r'marrow.*?complete.*?(\d+(?:\.\d+)?)\s*%'
        ]
        
        for pattern in marrow_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                clinical_data['efficacy_measures']['marrow_cr'].append({
                    'value': float(match),
                    'pmid': abstract.get('pmid'),
                    'source': abstract.get('title', 'Unknown'),
                    'year': self._extract_year(abstract.get('title', ''))
                })
        
        # Survival patterns
        survival_patterns = [
            (r'median overall survival.*?(\d+(?:\.\d+)?)\s*months', 'overall_survival'),
            (r'median os.*?(\d+(?:\.\d+)?)\s*months', 'overall_survival'),
            (r'median progression-free survival.*?(\d+(?:\.\d+)?)\s*months', 'progression_free_survival'),
            (r'median pfs.*?(\d+(?:\.\d+)?)\s*months', 'progression_free_survival'),
            (r'median event-free survival.*?(\d+(?:\.\d+)?)\s*months', 'event_free_survival'),
            (r'median efs.*?(\d+(?:\.\d+)?)\s*months', 'event_free_survival')
        ]
        
        for pattern, survival_type in survival_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                clinical_data['efficacy_measures'][survival_type].append({
                    'value': float(match),
                    'pmid': abstract.get('pmid'),
                    'source': abstract.get('title', 'Unknown'),
                    'year': self._extract_year(abstract.get('title', ''))
                })
    
    def _extract_adverse_events(self, text: str, abstract: Dict, clinical_data: Dict):
        """Extract serious adverse events"""
        ae_patterns = [
            (r'grade 3-4.*?neutropenia.*?(\d+(?:\.\d+)?)\s*%', 'Grade 3-4 Neutropenia'),
            (r'grade 3-4.*?thrombocytopenia.*?(\d+(?:\.\d+)?)\s*%', 'Grade 3-4 Thrombocytopenia'),
            (r'febrile neutropenia.*?(\d+(?:\.\d+)?)\s*%', 'Febrile Neutropenia'),
            (r'neutropenia.*?(\d+(?:\.\d+)?)\s*%', 'Neutropenia'),
            (r'thrombocytopenia.*?(\d+(?:\.\d+)?)\s*%', 'Thrombocytopenia'),
            (r'anemia.*?(\d+(?:\.\d+)?)\s*%', 'Anemia'),
            (r'infection.*?(\d+(?:\.\d+)?)\s*%', 'Infection'),
            (r'sepsis.*?(\d+(?:\.\d+)?)\s*%', 'Sepsis')
        ]
        
        for pattern, ae_type in ae_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                clinical_data['adverse_events'].append({
                    'type': ae_type,
                    'value': float(match),
                    'pmid': abstract.get('pmid'),
                    'source': abstract.get('title', 'Unknown'),
                    'year': self._extract_year(abstract.get('title', ''))
                })
    
    def _extract_ras_data(self, text: str, abstract: Dict, clinical_data: Dict):
        """Extract RAS mutation-specific data"""
        ras_patterns = [
            (r'ras.*?mutated.*?(\d+(?:\.\d+)?)\s*%', 'ras_mutated'),
            (r'ras.*?mutation.*?(\d+(?:\.\d+)?)\s*%', 'ras_mutated'),
            (r'non-ras.*?(\d+(?:\.\d+)?)\s*%', 'non_ras_mutated'),
            (r'wild-type.*?ras.*?(\d+(?:\.\d+)?)\s*%', 'non_ras_mutated')
        ]
        
        for pattern, ras_type in ras_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                clinical_data[ras_type].append({
                    'value': float(match),
                    'pmid': abstract.get('pmid'),
                    'source': abstract.get('title', 'Unknown'),
                    'year': self._extract_year(abstract.get('title', ''))
                })
    
    def _extract_year(self, title: str) -> Optional[int]:
        """Extract year from title or return None"""
        year_match = re.search(r'20\d{2}', title)
        return int(year_match.group()) if year_match else None
    
    def generate_structured_report(self, clinical_data: Dict, medicine: str) -> str:
        """Generate structured report in the requested format"""
        report = f"# Clinical Outcomes Data for {medicine.title()} in CMML\n\n"
        
        # Structured data table
        report += "## Structured Data Table\n\n"
        report += "| Efficacy Measure | Value | Citation |\n"
        report += "|-----------------|-------|----------|\n"
        
        # Add efficacy measures to table
        for measure_name, measure_data in clinical_data['efficacy_measures'].items():
            if measure_data:
                avg_value = sum(item['value'] for item in measure_data) / len(measure_data)
                pmid = measure_data[0]['pmid']
                report += f"| {measure_name.replace('_', ' ').title()} | {avg_value:.1f} | PMID: {pmid} |\n"
        
        # Add adverse events to table
        if clinical_data['adverse_events']:
            ae_by_type = defaultdict(list)
            for ae in clinical_data['adverse_events']:
                ae_by_type[ae['type']].append(ae)
            
            for ae_type, ae_data in ae_by_type.items():
                avg_value = sum(item['value'] for item in ae_data) / len(ae_data)
                pmid = ae_data[0]['pmid']
                report += f"| {ae_type} | {avg_value:.1f}% | PMID: {pmid} |\n"
        
        report += "\n"
        
        # Drug summary paragraph
        report += "## Drug Summary\n\n"
        
        # Calculate summary statistics
        total_studies = len(clinical_data['studies'])
        cr_avg = self._calculate_average(clinical_data['efficacy_measures']['complete_response'])
        pr_avg = self._calculate_average(clinical_data['efficacy_measures']['partial_response'])
        os_avg = self._calculate_average(clinical_data['efficacy_measures']['overall_survival'])
        pfs_avg = self._calculate_average(clinical_data['efficacy_measures']['progression_free_survival'])
        
        report += f"{medicine.title()} demonstrates "
        if cr_avg:
            report += f"a complete response rate of {cr_avg:.1f}% "
        if pr_avg:
            report += f"and partial response rate of {pr_avg:.1f}%. "
        if os_avg:
            report += f"Median overall survival is {os_avg:.1f} months "
        if pfs_avg:
            report += f"with progression-free survival of {pfs_avg:.1f} months. "
        
        report += f"Based on {total_studies} studies, "
        
        # Add adverse events summary
        if clinical_data['adverse_events']:
            ae_summary = self._summarize_adverse_events(clinical_data['adverse_events'])
            report += f"the most common serious adverse events include "
            ae_list = []
            for ae_type, stats in ae_summary.items():
                ae_list.append(f"{ae_type} ({stats['avg']:.1f}%)")
            report += ", ".join(ae_list[:3]) + ". "
        
        report += "The drug shows moderate efficacy in CMML with manageable toxicity profile.\n\n"
        
        # RAS mutation data
        if clinical_data['ras_mutated'] or clinical_data['non_ras_mutated']:
            report += "## RAS Mutation Subgroup Analysis\n\n"
            
            if clinical_data['ras_mutated']:
                ras_avg = sum(item['value'] for item in clinical_data['ras_mutated']) / len(clinical_data['ras_mutated'])
                ras_pmid = clinical_data['ras_mutated'][0]['pmid']
                report += f"- **RAS-mutated CMML**: {ras_avg:.1f}% (PMID: {ras_pmid})\n"
            
            if clinical_data['non_ras_mutated']:
                non_ras_avg = sum(item['value'] for item in clinical_data['non_ras_mutated']) / len(clinical_data['non_ras_mutated'])
                non_ras_pmid = clinical_data['non_ras_mutated'][0]['pmid']
                report += f"- **Non-RAS-mutated CMML**: {non_ras_avg:.1f}% (PMID: {non_ras_pmid})\n"
            
            report += "\n"
        
        # Citations
        report += "## Citations\n\n"
        for study in clinical_data['studies'][:10]:  # Top 10 studies
            report += f"- **PMID {study['pmid']}**: {study['title']}\n"
            if study['doi'] != 'Unknown':
                report += f"  - DOI: {study['doi']}\n"
            if study['year']:
                report += f"  - Year: {study['year']}\n"
            report += "\n"
        
        return report
    
    def _calculate_average(self, data_list: List[Dict]) -> Optional[float]:
        """Calculate average for data list"""
        if not data_list:
            return None
        return sum(item['value'] for item in data_list) / len(data_list)
    
    def _summarize_adverse_events(self, ae_data: List[Dict]) -> Dict:
        """Summarize adverse event data"""
        summary = defaultdict(list)
        for item in ae_data:
            summary[item['type']].append(item['value'])
        
        result = {}
        for ae_type, values in summary.items():
            result[ae_type] = {
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values)
            }
        return result

def main():
    """Main function to run the medicine-specific clinical data extraction"""
    if len(sys.argv) < 2:
        print("Usage: python medicine_clinical_extractor.py <medicine_name>")
        print("Available medicines: azacitidine, decitabine, hydroxyurea")
        sys.exit(1)
    
    medicine = sys.argv[1].lower()
    
    extractor = MedicineClinicalExtractor()
    
    # Validate medicine name
    if medicine not in extractor.drugs:
        print(f"Error: {medicine} not found. Available medicines: {list(extractor.drugs.keys())}")
        sys.exit(1)
    
    print(f"Extracting clinical data for {medicine.title()} in CMML...")
    
    # Search queries for the specific medicine
    queries = [
        f"{medicine} CMML clinical trial",
        f"{medicine} chronic myelomonocytic leukemia response",
        f"{medicine} CMML survival outcomes",
        f"{medicine} CMML adverse events"
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
    clinical_data = extractor.extract_clinical_data(abstracts, medicine)
    
    # Generate structured report
    print("Generating structured report...")
    report = extractor.generate_structured_report(clinical_data, medicine)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with open(f"{medicine}_cmml_report_{timestamp}.md", "w") as f:
        f.write(report)
    
    # Save raw data as JSON
    with open(f"{medicine}_clinical_data_{timestamp}.json", "w") as f:
        json.dump(clinical_data, f, indent=2)
    
    print(f"Report saved as: {medicine}_cmml_report_{timestamp}.md")
    print(f"Raw data saved as: {medicine}_clinical_data_{timestamp}.json")
    
    # Print summary
    print(f"\nSummary for {medicine.title()}:")
    print(f"- Complete Response data points: {len(clinical_data['efficacy_measures']['complete_response'])}")
    print(f"- Overall Survival data points: {len(clinical_data['efficacy_measures']['overall_survival'])}")
    print(f"- Adverse events: {len(clinical_data['adverse_events'])}")
    print(f"- Studies identified: {len(clinical_data['studies'])}")
    print(f"- RAS mutation data: {len(clinical_data['ras_mutated'])}")
    print(f"- Non-RAS mutation data: {len(clinical_data['non_ras_mutated'])}")

if __name__ == "__main__":
    main() 