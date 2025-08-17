
import json
import statistics

def get_value(study, key, subkey=None):
    if subkey:
        return study.get(key, {}).get(subkey)
    return study.get(key)

def calculate_stats(data):
    if not data:
        return {"mean": "N/A", "median": "N/A"}
    
    filtered_data = [x for x in data if x is not None]
    if not filtered_data:
        return {"mean": "N/A", "median": "N/A"}

    return {
        "mean": round(statistics.mean(filtered_data), 2),
        "median": round(statistics.median(filtered_data), 2)
    }

def analyze_detailed_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    drugs = {
        "Azacitidine": data.get("azacitidine", []),
        "Decitabine": data.get("decitabine", []),
        "Hydroxyurea": data.get("hydroxyurea", [])
    }

    results = {}

    for drug_name, studies in drugs.items():
        results[drug_name] = {
            "aggregate": {},
            "ras_mutant": {},
            "non_ras_mutant": {}
        }

        # Efficacy Metrics
        for metric in ["complete_response", "partial_response", "marrow_complete_response", "marrow_optimal_response", "pfs_median", "os_median", "efs_median"]:
            # Aggregate
            agg_data = [get_value(s, metric) for s in studies]
            results[drug_name]["aggregate"][metric] = calculate_stats(agg_data)

            # RAS Mutant
            ras_data = [get_value(s, "ras_mutant_data", metric.replace("_median", "").replace("response","rate")) for s in studies]
            results[drug_name]["ras_mutant"][metric] = calculate_stats(ras_data)

            # Non-RAS Mutant
            non_ras_data = [get_value(s, "non_ras_mutant_data", metric.replace("_median", "").replace("response","rate")) for s in studies]
            results[drug_name]["non_ras_mutant"][metric] = calculate_stats(non_ras_data)

        # Adverse Events
        # Aggregate
        agg_sae = [get_value(s, "sae_frequency") for s in studies]
        results[drug_name]["aggregate"]["sae_frequency"] = calculate_stats(agg_sae)

        # RAS Mutant
        ras_sae = [get_value(s, "ras_mutant_data", "sae_rate") for s in studies]
        results[drug_name]["ras_mutant"]["sae_frequency"] = calculate_stats(ras_sae)

        # Non-RAS Mutant
        non_ras_sae = [get_value(s, "non_ras_mutant_data", "sae_rate") for s in studies]
        results[drug_name]["non_ras_mutant"]["sae_frequency"] = calculate_stats(non_ras_sae)

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    analyze_detailed_data("/Users/hennykim/Downloads/pharma_arca/cmml_research/data/cmml_detailed_outcomes.json")
