# CMML Drug Analysis Dashboard

A comprehensive web dashboard for analyzing clinical efficacy and adverse events data for CMML (Chronic Myelomonocytic Leukemia) treatments.

## Features

- **Clinical Efficacy Data**: Complete response rates, overall response rates, progression-free survival, and overall survival data
- **Adverse Events Analysis**: Comprehensive adverse events data extracted using LLM technology
- **Drug Comparison**: Side-by-side comparison of Azacitidine, Decitabine, and Hydroxyurea
- **Interactive Interface**: Click on metrics to view source papers and detailed information
- **Real-time Data**: Live data loading with cache busting

## Data Sources

- **Azacitidine**: 169 papers (75 with clinical data, 18 with adverse events)
- **Decitabine**: 125 papers (51 with clinical data, comprehensive adverse events)
- **Hydroxyurea**: 4 papers with clinical and adverse events data

## Technologies Used

- HTML5, CSS3, JavaScript (ES6+)
- Vercel for deployment
- LLM-extracted clinical data
- PubMed integration

## Deployment

This dashboard is deployed on Vercel and accessible via web browser.

## Data Files

- `simple_dashboard.html` - Main dashboard interface
- `updated_dashboard_data.json` - Aggregated dashboard data
- `clinical_efficacy_azacitidine.json` - Azacitidine clinical efficacy data
- `adverse_event_comprehensive.json` - Comprehensive adverse events data
- `Decitabine_extracted.json` - Decitabine clinical data
- `Hydroxyurea_extracted.json` - Hydroxyurea clinical data

## Usage

1. Open the dashboard in a web browser
2. View paper counts and summary statistics
3. Click on drug cards to see detailed metrics
4. Click on specific metrics to view source papers
5. Use modal popups to explore detailed paper information

## Research Context

This dashboard provides evidence-based insights for CMML treatment decisions, combining clinical efficacy and safety data from peer-reviewed literature.
# parca_cmml_final
# parca_cmml_final
