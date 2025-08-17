import json
import numpy as np
import os

def get_mean(arr):
    return np.mean(arr) if arr else None

def get_median(arr):
    return np.median(arr) if arr else None

# Input/output paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
root_input = os.path.join(BASE_DIR, 'cmml_detailed_outcomes.json')
data_input = os.path.join(BASE_DIR, 'data', 'cmml_detailed_outcomes.json')
output_file = os.path.join(BASE_DIR, 'summarized_outcomes.json')

# Use comprehensive adverse event data for full dataset
ae_file = os.path.join(BASE_DIR, 'adverse_event_comprehensive.json')
clinical_file = data_input

# Load both datasets
if os.path.exists(ae_file):
    print(f"Loading comprehensive dataset from {ae_file}")
    with open(ae_file, 'r') as f:
        comprehensive_data = json.load(f)
else:
    comprehensive_data = None

# Load clinical data for efficacy metrics
if os.path.exists(clinical_file):
    print(f"Loading clinical data from {clinical_file}")
    input_file = clinical_file
elif os.path.exists(root_input):
    print(f"Loading clinical data from {root_input}")
    input_file = root_input
else:
    raise FileNotFoundError('No clinical outcomes data found')

with open(input_file, 'r') as f:
    data = json.load(f)

results = {}

drugs_to_process = ['azacitidine', 'decitabine', 'hydroxyurea']

for drug in drugs_to_process:
    studies = data.get(drug, [])
    
    cr_rates = [s['complete_response'] for s in studies if s.get('complete_response') is not None]
    orr_rates = [(s.get('complete_response') or 0) + (s.get('partial_response') or 0) + (s.get('marrow_complete_response') or 0) for s in studies if (s.get('complete_response') is not None or s.get('partial_response') is not None or s.get('marrow_complete_response') is not None)]
    pfs_medians = [s['pfs_median'] for s in studies if s.get('pfs_median') is not None]
    os_medians = [s['os_median'] for s in studies if s.get('os_median') is not None]
    sae_frequencies = [s['sae_frequency'] for s in studies if s.get('sae_frequency') is not None]

    results[drug] = {
        'efficacy': {
            'cr_mean': get_mean(cr_rates),
            'cr_median': get_median(cr_rates),
            'orr_mean': get_mean(orr_rates),
            'orr_median': get_median(orr_rates),
        },
        'safety': {
            'sae_mean': get_mean(sae_frequencies),
            'sae_median': get_median(sae_frequencies),
        },
        'survival': {
            'pfs_mean': get_mean(pfs_medians),
            'pfs_median': get_median(pfs_medians),
            'os_mean': get_mean(os_medians),
            'os_median': get_median(os_medians),
        }
    }

# Combined Azacitidine and Decitabine
aza_dec_studies = data.get('azacitidine', []) + data.get('decitabine', [])
cr_rates_combined = [s['complete_response'] for s in aza_dec_studies if s.get('complete_response') is not None]
orr_rates_combined = [(s.get('complete_response') or 0) + (s.get('partial_response') or 0) + (s.get('marrow_complete_response') or 0) for s in aza_dec_studies if (s.get('complete_response') is not None or s.get('partial_response') is not None or s.get('marrow_complete_response') is not None)]
pfs_medians_combined = [s['pfs_median'] for s in aza_dec_studies if s.get('pfs_median') is not None]
os_medians_combined = [s['os_median'] for s in aza_dec_studies if s.get('os_median') is not None]

results['azacitidine_decitabine_combined'] = {
    'efficacy': {
        'cr_mean': get_mean(cr_rates_combined),
        'cr_median': get_median(cr_rates_combined),
        'orr_mean': get_mean(orr_rates_combined),
        'orr_median': get_median(orr_rates_combined),
    },
    'survival': {
        'pfs_mean': get_mean(pfs_medians_combined),
        'pfs_median': get_median(pfs_medians_combined),
        'os_mean': get_mean(os_medians_combined),
        'os_median': get_median(os_medians_combined),
    }
}

# Add paper count metadata
if comprehensive_data:
    results['_metadata'] = {
        'comprehensive_paper_counts': {
            'azacitidine': len(comprehensive_data.get('azacitidine', [])),
            'decitabine': len(comprehensive_data.get('decitabine', [])),
            'total_comprehensive': sum(len(papers) for papers in comprehensive_data.values())
        },
        'clinical_data_paper_counts': {
            'azacitidine': len(data.get('azacitidine', [])),
            'decitabine': len(data.get('decitabine', [])),
            'hydroxyurea': len(data.get('hydroxyurea', [])),
            'total_clinical': sum(len(papers) for drug, papers in data.items() if drug != 'extraction_metadata')
        }
    }

with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"Successfully summarized the data from {input_file} and saved to {output_file}")

if comprehensive_data:
    print("\nCOMPREHENSIVE DATASET (for paper counts):")
    for drug in comprehensive_data:
        print(f"  {drug.capitalize()}: {len(comprehensive_data[drug])} papers")
    total_comprehensive = sum(len(papers) for papers in comprehensive_data.values())
    print(f"  Total comprehensive: {total_comprehensive} papers")

print("\nCLINICAL DATA SUBSET (for efficacy/survival metrics):")
for drug in drugs_to_process:
    count = len(data.get(drug, []))
    print(f"  {drug.capitalize()}: {count} papers with clinical data")
print(f"  Azacitidine + Decitabine combined: {len(aza_dec_studies)} papers with clinical data")
print(f"  Total clinical data papers: {sum(len(data.get(drug, [])) for drug in drugs_to_process)}")