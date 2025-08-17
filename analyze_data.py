
import json
import statistics

def get_orr(study):
    cr = study.get("complete_response") or 0
    pr = study.get("partial_response") or 0
    mcr = study.get("marrow_complete_response") or 0
    return cr + pr + mcr

def calculate_stats(data):
    if not data:
        return {"mean": "N/A", "median": "N/A"}
    
    # Filter out None values before calculation
    filtered_data = [x for x in data if x is not None]
    if not filtered_data:
        return {"mean": "N/A", "median": "N/A"}

    return {
        "mean": round(statistics.mean(filtered_data), 2),
        "median": round(statistics.median(filtered_data), 2)
    }

def analyze_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    products = ["azacitidine", "decitabine", "hydroxyurea"]
    results = {}

    for product in products:
        studies = data.get(product, [])
        
        cr_rates = [study.get("complete_response") for study in studies]
        orr_rates = [get_orr(study) for study in studies]
        sae_frequencies = [study.get("sae_frequency") for study in studies]
        # duration_of_therapy = # This data is not available in the JSON
        pfs_medians = [study.get("pfs_median") for study in studies]
        os_medians = [study.get("os_median") for study in studies]

        results[product] = {
            "Efficacy (CR)": calculate_stats(cr_rates),
            "Efficacy (ORR)": calculate_stats(orr_rates),
            "Adverse Events (SAE)": calculate_stats(sae_frequencies),
            "Progression Free Survival (PFS)": calculate_stats(pfs_medians),
            "Overall Survival (OS)": calculate_stats(os_medians)
        }

    # Combined azacitidine and decitabine
    aza_dec_studies = data.get("azacitidine", []) + data.get("decitabine", [])
    
    cr_rates_combined = [study.get("complete_response") for study in aza_dec_studies]
    orr_rates_combined = [get_orr(study) for study in aza_dec_studies]
    pfs_medians_combined = [study.get("pfs_median") for study in aza_dec_studies]
    os_medians_combined = [study.get("os_median") for study in aza_dec_studies]
    
    results["azacitidine_decitabine_combined"] = {
        "Efficacy (CR)": calculate_stats(cr_rates_combined),
        "Efficacy (ORR)": calculate_stats(orr_rates_combined),
        "Progression Free Survival (PFS)": calculate_stats(pfs_medians_combined),
        "Overall Survival (OS)": calculate_stats(os_medians_combined)
    }

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    analyze_data("/Users/hennykim/Downloads/pharma_arca/cmml_research/data/cmml_detailed_outcomes.json")
