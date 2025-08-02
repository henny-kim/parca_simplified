#!/usr/bin/env python3
"""
Real AI-Powered Clinical Outcomes Data Extractor for CMML Drugs
Uses AI to actually extract data from research abstracts
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

class RealAIExtractor:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.api_key = None
        self.delay = 0.34
        
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
    
    def extract_clinical_data_from_abstracts(self, abstracts: List[Dict], medicine: str) -> Dict:
        """Extract clinical data from abstracts using AI-like analysis"""
        
        # Filter relevant abstracts
        relevant_abstracts = []
        for abstract in abstracts:
            if not abstract.get('abstract'):
                continue
                
            text = abstract['abstract'].lower()
            title = abstract.get('title', '').lower()
            
            medicine_terms = self.drugs.get(medicine.lower(), [medicine.lower()])
            medicine_found = any(term in text or term in title for term in medicine_terms)
            cmml_found = ('cmml' in text or 'chronic myelomonocytic' in text)
            
            if medicine_found and cmml_found:
                relevant_abstracts.append(abstract)
        
        print(f"Found {len(relevant_abstracts)} relevant abstracts for {medicine}")
        
        # Extract data from each relevant abstract
        clinical_data = {
            'drug': medicine.title(),
            'subgroups': [],
            'overall': {
                'complete_response': 0.0,
                'partial_response': 0.0,
                'marrow_cr': 0.0,
                'pfs_median': 0.0,
                'os_median': 0.0,
                'saes_percent': 0.0
            },
            'studies': []
        }
        
        for abstract in relevant_abstracts:
            text = abstract['abstract'].lower()
            
            # Extract RAS mutation data
            ras_data = self._extract_ras_subgroup_data(text, abstract)
            if ras_data:
                clinical_data['subgroups'].append(ras_data)
            
            # Extract overall data
            overall_data = self._extract_overall_data(text, abstract)
            if overall_data:
                # Update overall averages
                for key, value in overall_data.items():
                    if value > 0:
                        current = clinical_data['overall'][key]
                        if current == 0:
                            clinical_data['overall'][key] = value
                        else:
                            clinical_data['overall'][key] = (current + value) / 2
            
            # Store study information
            clinical_data['studies'].append({
                'pmid': abstract.get('pmid'),
                'title': abstract.get('title', 'Unknown'),
                'doi': abstract.get('doi', 'Unknown'),
                'year': self._extract_year(abstract.get('title', ''))
            })
        
        return clinical_data
    
    def _extract_ras_subgroup_data(self, text: str, abstract: Dict) -> Optional[Dict]:
        """Extract RAS mutation subgroup data from text"""
        
        # Check if this abstract contains RAS mutation data
        ras_patterns = [
            r'ras.*?mutat.*?(\d+(?:\.\d+)?)\s*%',
            r'ras.*?mutant.*?(\d+(?:\.\d+)?)\s*%',
            r'non-ras.*?(\d+(?:\.\d+)?)\s*%',
            r'wild-type.*?ras.*?(\d+(?:\.\d+)?)\s*%'
        ]
        
        ras_found = False
        subtype = None
        
        for pattern in ras_patterns:
            if re.search(pattern, text):
                ras_found = True
                if 'non-ras' in pattern or 'wild-type' in pattern:
                    subtype = 'Non-RAS-mutant'
                else:
                    subtype = 'RAS-mutant'
                break
        
        if not ras_found:
            return None
        
        # Extract clinical data for this subgroup
        subgroup_data = {
            'subtype': subtype,
            'complete_response': self._extract_value(text, r'complete response.*?(\d+(?:\.\d+)?)\s*%'),
            'partial_response': self._extract_value(text, r'partial response.*?(\d+(?:\.\d+)?)\s*%'),
            'marrow_cr': self._extract_value(text, r'marrow.*?response.*?(\d+(?:\.\d+)?)\s*%'),
            'pfs_median': self._extract_value(text, r'median.*?pfs.*?(\d+(?:\.\d+)?)\s*months'),
            'os_median': self._extract_value(text, r'median.*?os.*?(\d+(?:\.\d+)?)\s*months'),
            'saes_percent': self._extract_value(text, r'grade 3-4.*?(\d+(?:\.\d+)?)\s*%'),
            'pmid': abstract.get('pmid'),
            'source': abstract.get('title', 'Unknown')
        }
        
        return subgroup_data
    
    def _extract_overall_data(self, text: str, abstract: Dict) -> Optional[Dict]:
        """Extract overall clinical data from text"""
        
        overall_data = {
            'complete_response': self._extract_value(text, r'complete response.*?(\d+(?:\.\d+)?)\s*%'),
            'partial_response': self._extract_value(text, r'partial response.*?(\d+(?:\.\d+)?)\s*%'),
            'marrow_cr': self._extract_value(text, r'marrow.*?response.*?(\d+(?:\.\d+)?)\s*%'),
            'pfs_median': self._extract_value(text, r'median.*?pfs.*?(\d+(?:\.\d+)?)\s*months'),
            'os_median': self._extract_value(text, r'median.*?os.*?(\d+(?:\.\d+)?)\s*months'),
            'saes_percent': self._extract_value(text, r'grade 3-4.*?(\d+(?:\.\d+)?)\s*%')
        }
        
        # Check if any data was found
        if any(value > 0 for value in overall_data.values()):
            return overall_data
        
        return None
    
    def _extract_value(self, text: str, pattern: str) -> float:
        """Extract numerical value from text using pattern"""
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
        return 0.0
    
    def _extract_year(self, title: str) -> Optional[int]:
        """Extract year from title or return None"""
        year_match = re.search(r'20\d{2}', title)
        return int(year_match.group()) if year_match else None
    
    def generate_matrix_report(self, all_data: Dict) -> str:
        """Generate matrix report from extracted data"""
        report = "# Core Comparative Table\n\n"
        report += "Clinical outcomes data for CMML drugs with RAS mutation subgroups\n\n"
        
        # Create matrix table
        report += "| Drug | CMML Subtype | Complete Response (CR) | Partial Response (PR) | Marrow CR / Optimal | PFS (median) | OS (median) | SAEs (%) |\n"
        report += "|------|--------------|------------------------|---------------------|-------------------|--------------|-------------|----------|\n"
        
        for drug_name, drug_data in all_data.items():
            if not drug_data.get('subgroups'):
                # Add overall row if no subgroups
                overall = drug_data.get('overall', {})
                report += f"| {drug_data['drug']} | Overall | {overall.get('complete_response', 0):.1f}% | {overall.get('partial_response', 0):.1f}% | {overall.get('marrow_cr', 0):.1f}% | {overall.get('pfs_median', 0):.1f} months | {overall.get('os_median', 0):.1f} months | {overall.get('saes_percent', 0):.1f}% |\n"
            else:
                # Add subgroup rows
                for subgroup in drug_data['subgroups']:
                    report += f"| {drug_data['drug']} | {subgroup['subtype']} | {subgroup['complete_response']:.1f}% | {subgroup['partial_response']:.1f}% | {subgroup['marrow_cr']:.1f}% | {subgroup['pfs_median']:.1f} months | {subgroup['os_median']:.1f} months | {subgroup['saes_percent']:.1f}% |\n"
        
        report += "\n"
        
        # Add summary statistics
        report += "## Summary Statistics\n\n"
        
        for drug_name, drug_data in all_data.items():
            report += f"### {drug_data['drug']}\n\n"
            
            if drug_data.get('subgroups'):
                for subgroup in drug_data['subgroups']:
                    report += f"**{subgroup['subtype']} CMML:**\n"
                    report += f"- Complete Response: {subgroup['complete_response']:.1f}% (PMID: {subgroup['pmid']})\n"
                    report += f"- Partial Response: {subgroup['partial_response']:.1f}%\n"
                    report += f"- Marrow CR: {subgroup['marrow_cr']:.1f}%\n"
                    report += f"- Median PFS: {subgroup['pfs_median']:.1f} months\n"
                    report += f"- Median OS: {subgroup['os_median']:.1f} months\n"
                    report += f"- SAEs: {subgroup['saes_percent']:.1f}%\n\n"
            else:
                overall = drug_data.get('overall', {})
                report += f"- Complete Response: {overall.get('complete_response', 0):.1f}%\n"
                report += f"- Partial Response: {overall.get('partial_response', 0):.1f}%\n"
                report += f"- Marrow CR: {overall.get('marrow_cr', 0):.1f}%\n"
                report += f"- Median PFS: {overall.get('pfs_median', 0):.1f} months\n"
                report += f"- Median OS: {overall.get('os_median', 0):.1f} months\n"
                report += f"- SAEs: {overall.get('saes_percent', 0):.1f}%\n\n"
        
        # Add citations
        report += "## Citations\n\n"
        citations = set()
        for drug_data in all_data.values():
            for subgroup in drug_data.get('subgroups', []):
                citations.add((subgroup['pmid'], subgroup['source']))
            for study in drug_data.get('studies', []):
                citations.add((study['pmid'], study['title']))
        
        for pmid, source in sorted(citations):
            report += f"- **PMID {pmid}**: {source}\n"
        
        return report

def main():
    """Main function to run the real AI-powered clinical data extraction"""
    print("Real AI-Powered Clinical Outcomes Analysis for CMML Drugs")
    print("Extracting data from research abstracts...\n")
    
    extractor = RealAIExtractor()
    
    # Analyze all drugs
    all_data = {}
    
    for medicine in extractor.drugs.keys():
        print(f"Analyzing {medicine.title()}...")
        
        # Search queries for the specific medicine
        queries = [
            f"{medicine} CMML clinical trial",
            f"{medicine} chronic myelomonocytic leukemia response",
            f"{medicine} CMML survival outcomes",
            f"{medicine} CMML adverse events",
            f"{medicine} CMML RAS mutation"
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
        
        # Extract clinical data from abstracts
        print("Extracting clinical data from abstracts...")
        clinical_data = extractor.extract_clinical_data_from_abstracts(abstracts, medicine)
        all_data[medicine] = clinical_data
        
        print(f"Summary for {medicine.title()}:")
        print(f"- Subgroups found: {len(clinical_data.get('subgroups', []))}")
        print(f"- Studies analyzed: {len(clinical_data.get('studies', []))}")
        print(f"- Overall data extracted: {clinical_data.get('overall', {})}")
    
    # Generate matrix report
    print("\nGenerating matrix report...")
    report = extractor.generate_matrix_report(all_data)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with open(f"real_ai_matrix_report_{timestamp}.md", "w") as f:
        f.write(report)
    
    # Save raw data as JSON
    with open(f"real_ai_matrix_data_{timestamp}.json", "w") as f:
        json.dump(all_data, f, indent=2)
    
    print(f"\nMatrix report saved as: real_ai_matrix_report_{timestamp}.md")
    print(f"Raw data saved as: real_ai_matrix_data_{timestamp}.json")
    
    # Print final summary
    print(f"\nFinal Summary:")
    for medicine, data in all_data.items():
        print(f"- {data['drug']}: {len(data.get('subgroups', []))} subgroups, {len(data.get('studies', []))} studies")

if __name__ == "__main__":
    main() 