#!/usr/bin/env python3
import requests
import time
import json
import re

def test_abstract_fetching():
    pmids = ['36455187', '38106568', '39437109']
    
    for pmid in pmids:
        try:
            print(f"\n--- Testing PMID {pmid} ---")
            
            # Try different API calls
            urls = [
                f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=text&rettype=abstract',
                f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=text&rettype=medline',
                f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml&rettype=abstract',
                f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json&tool=test&email=test@test.com'
            ]
            
            for i, url in enumerate(urls):
                print(f"  Method {i+1}: {url.split('rettype=')[-1] if 'rettype=' in url else 'esummary'}")
                response = requests.get(url)
                if response.status_code == 200:
                    text = response.text
                    if 'rettype=abstract' in url:
                        # Look for abstract in text format
                        abstract_match = re.search(r'AB\s+-\s+(.*?)(?=\n[A-Z]{2}\s+-|\n\n|\Z)', text, re.DOTALL)
                        if abstract_match:
                            abstract = abstract_match.group(1).strip()
                            print(f"    ✓ Abstract found: {len(abstract)} chars")
                            print(f"    Preview: {abstract[:100]}...")
                        else:
                            print(f"    ✗ No abstract pattern found")
                    elif 'rettype=medline' in url:
                        # Look for abstract in MEDLINE format
                        abstract_match = re.search(r'AB\s+-\s+(.*?)(?=\n[A-Z]{2}\s+-|\n\n|\Z)', text, re.DOTALL)
                        if abstract_match:
                            abstract = abstract_match.group(1).strip()
                            print(f"    ✓ Abstract found: {len(abstract)} chars")
                            print(f"    Preview: {abstract[:100]}...")
                        else:
                            print(f"    ✗ No abstract pattern found")
                    elif 'retmode=xml' in url:
                        # Look for abstract in XML format
                        abstract_match = re.search(r'<AbstractText>(.*?)</AbstractText>', text, re.DOTALL)
                        if abstract_match:
                            abstract = abstract_match.group(1).strip()
                            print(f"    ✓ Abstract found: {len(abstract)} chars")
                            print(f"    Preview: {abstract[:100]}...")
                        else:
                            print(f"    ✗ No abstract in XML")
                    else:
                        # JSON format
                        try:
                            data = response.json()
                            abstract = data['result'][pmid].get('abstract', '')
                            if abstract:
                                print(f"    ✓ Abstract found: {len(abstract)} chars")
                                print(f"    Preview: {abstract[:100]}...")
                            else:
                                print(f"    ✗ No abstract in JSON")
                        except:
                            print(f"    ✗ JSON parsing failed")
                else:
                    print(f"    ✗ HTTP {response.status_code}")
                time.sleep(0.5)
                
        except Exception as e:
            print(f'Error fetching PMID {pmid}: {e}')

if __name__ == "__main__":
    test_abstract_fetching()
