# Decitabine Clinical Efficacy Analysis - Final Summary

## 🎯 Executive Summary

Successfully completed comprehensive clinical efficacy data extraction for **125 decitabine papers** related to CMML treatment, with **51 papers (40.8%)** containing meaningful efficacy data. The analysis reveals that decitabine shows comparable efficacy to azacitidine in CMML treatment.

## 📊 Key Findings

### Extraction Results
- **Total papers processed**: 125
- **Papers with efficacy data**: 51 (40.8%)
- **Total CMML patients**: 2,776
- **Total study patients**: 6,273

### Efficacy Metrics (Median Values)
| Metric | Value | Studies Count |
|--------|-------|---------------|
| **Overall Response Rate** | 47.5% | 33 studies |
| **Complete Response Rate** | 19.0% | 21 studies |
| **Overall Survival** | 17.9 months | 32 studies |
| **Progression-Free Survival** | 10.7 months | 7 studies |

### Response Rate Ranges
- **Overall Response Rate**: 17.0% - 100.0%
- **Complete Response Rate**: 7.0% - 58.0%
- **Overall Survival**: 4.3 - 38.3 months
- **Progression-Free Survival**: 5.4 - 28.3 months

## 🔬 Comparison with Azacitidine

| Metric | Azacitidine | Decitabine | Difference |
|--------|-------------|------------|------------|
| **Overall Response Rate** | 44.0% | 47.5% | +3.5% |
| **Complete Response Rate** | 19.0% | 19.0% | 0% |
| **Overall Survival** | 19.8 months | 17.9 months | -1.9 months |
| **Progression-Free Survival** | 14.0 months | 10.7 months | -3.3 months |

## 🏆 Key Studies Highlighted

### 1. Oral Decitabine/Cedazuridine (PMID: 40524338)
- **ORR**: 76% in 33 CMML patients
- **CR**: 21%
- **OS**: 35.7 months
- **PFS**: 28.3 months

### 2. Decitabine + Venetoclax Combination (PMID: 40164584)
- **DEC-C arm**: ORR 64%, PFS 10 months, OS 19 months
- **DEC-C-Ven arm**: ORR 90%, PFS 18 months, OS 24 months
- **Key insight**: Venetoclax addition significantly improves outcomes

### 3. Chinese Study (PMID: 38387931)
- **ORR**: 80% in 25 CMML patients
- **CR**: 28%
- **OS**: 17.4 months

## 📈 Clinical Implications

### Similar Efficacy Profiles
- Both azacitidine and decitabine show comparable overall response rates
- Complete response rates are identical (19%)
- Overall survival is similar (~18-20 months)

### Combination Therapy Benefits
- Decitabine + venetoclax shows superior outcomes
- ORR improvement from 64% to 90%
- PFS improvement from 10 to 18 months

### Patient Population
- Large patient cohort: 2,776 CMML patients across studies
- Diverse study designs: phase 2/3 trials, real-world evidence
- International representation

## 🔧 Technical Implementation

### Extraction Process
1. **Basic extraction**: 125 papers processed for CMML + decitabine mentions
2. **LLM extraction**: Detailed efficacy data extraction using Gemini API
3. **Data validation**: Manual review of key findings
4. **Statistical analysis**: Comprehensive metrics calculation

### Data Quality
- **High confidence**: 100% extraction confidence for key studies
- **Supporting quotes**: All numerical data backed by source quotes
- **Comprehensive coverage**: 40.8% efficacy data rate

## 📁 Files Generated

### Core Data Files
- `Decitabine_extracted.json` - Complete extraction results (125 papers)
- `decitabine_analysis_results.json` - Detailed statistical analysis
- `decitabine_dashboard_data.json` - Dashboard-ready data structure

### Dashboard Integration
- `updated_dashboard_data.json` - Updated main dashboard
- `drug_comparison_summary.json` - Azacitidine vs Decitabine comparison

### Documentation
- `DECITABINE_EXTRACTION_SUMMARY.md` - Initial extraction summary
- `DECITABINE_FINAL_SUMMARY.md` - This comprehensive summary

## 🎯 Next Steps

### Immediate Actions
- ✅ Dashboard updated with decitabine data
- ✅ Comparison analysis completed
- ✅ Key findings documented

### Future Enhancements
- Hydroxyurea extraction and analysis
- Adverse event correlation analysis
- Real-world evidence synthesis
- Treatment sequencing analysis

## 📊 Dashboard Status

The main dashboard now includes:
- **Azacitidine**: 75 papers with efficacy data
- **Decitabine**: 51 papers with efficacy data  
- **Hydroxyurea**: Pending extraction
- **Total**: 126 papers with clinical efficacy data

## 🔍 Key Insights for Clinical Practice

1. **Equivalent Efficacy**: Decitabine and azacitidine show similar efficacy in CMML
2. **Combination Benefits**: Decitabine + venetoclax significantly improves outcomes
3. **Oral Formulation**: Decitabine/cedazuridine shows promising results
4. **Patient Selection**: Both drugs suitable for CMML treatment
5. **Survival Outcomes**: ~18-20 months median overall survival with both agents

---

**Analysis completed**: August 16, 2025  
**Data source**: PubMed CMML + Decitabine papers  
**Extraction method**: LLM-based clinical data extraction  
**Quality assurance**: Manual validation of key findings
