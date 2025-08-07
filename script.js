document.addEventListener('DOMContentLoaded', () => {
    fetchData();
});

async function fetchData() {
    try {
        const response = await fetch('data/cmml_detailed_outcomes.json');
        const data = await response.json();
        displayData(data);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function displayData(data) {
    const content = document.querySelector('.dashboard-content');
    content.innerHTML = ''; // Clear existing content

    const drugs = ['azacitidine', 'decitabine', 'hydroxyurea']; // Maintain order

    drugs.forEach(drugKey => {
        if (data[drugKey]) {
            const drugCard = createDrugCard(drugKey, data[drugKey]);
            content.appendChild(drugCard);
        }
    });
}

function createDrugCard(drugName, drugData) {
    const card = document.createElement('div');
    card.classList.add('drug-card');

    const title = document.createElement('h2');
    title.textContent = drugName.charAt(0).toUpperCase() + drugName.slice(1);
    card.appendChild(title);

    // Efficacy Measures
    const efficacySection = document.createElement('div');
    efficacySection.innerHTML = '<h3>Efficacy Measures</h3>';
    const efficacyList = document.createElement('ul');
    
    const addEfficacyItem = (label, value, unit = '') => {
        if (value !== null) {
            const item = document.createElement('li');
            item.textContent = `${label}: ${value}${unit}`;
            efficacyList.appendChild(item);
        }
    };

    // Aggregate efficacy data for overall view
    const aggregateEfficacy = {
        complete_response: [],
        partial_response: [],
        marrow_complete_response: [],
        marrow_optimal_response: [],
        pfs_median: [],
        os_median: [],
        efs_median: []
    };

    drugData.forEach(study => {
        if (study.complete_response !== null) aggregateEfficacy.complete_response.push(study.complete_response);
        if (study.partial_response !== null) aggregateEfficacy.partial_response.push(study.partial_response);
        if (study.marrow_complete_response !== null) aggregateEfficacy.marrow_complete_response.push(study.marrow_complete_response);
        if (study.marrow_optimal_response !== null) aggregateEfficacy.marrow_optimal_response.push(study.marrow_optimal_response);
        if (study.pfs_median !== null) aggregateEfficacy.pfs_median.push(study.pfs_median);
        if (study.os_median !== null) aggregateEfficacy.os_median.push(study.os_median);
        if (study.efs_median !== null) aggregateEfficacy.efs_median.push(study.efs_median);
    });

    const getAverage = (arr) => arr.length ? (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(1) : 'N/A';

    addEfficacyItem('Complete Response', getAverage(aggregateEfficacy.complete_response), '%');
    addEfficacyItem('Partial Response', getAverage(aggregateEfficacy.partial_response), '%');
    addEfficacyItem('Marrow Complete Response', getAverage(aggregateEfficacy.marrow_complete_response), '%');
    addEfficacyItem('Marrow Optimal Response', getAverage(aggregateEfficacy.marrow_optimal_response), '%');
    addEfficacyItem('PFS Median', getAverage(aggregateEfficacy.pfs_median), ' months');
    addEfficacyItem('OS Median', getAverage(aggregateEfficacy.os_median), ' months');
    addEfficacyItem('EFS Median', getAverage(aggregateEfficacy.efs_median), ' months');

    efficacySection.appendChild(efficacyList);
    card.appendChild(efficacySection);

    // RAS Mutation Subgroup Analysis
    const rasSection = document.createElement('div');
    rasSection.innerHTML = '<h3>RAS Mutation Subgroup Analysis</h3>';
    const rasList = document.createElement('ul');
    let hasRasData = false;

    drugData.forEach(study => {
        if (study.ras_mutant_data) {
            hasRasData = true;
            const item = document.createElement('li');
            item.innerHTML = `<strong>RAS-mutant:</strong> CR: ${study.ras_mutant_data.cr_rate || 'N/A'}%, OS: ${study.ras_mutant_data.os_median || 'N/A'} months (PMID: ${study.pmid})`;
            rasList.appendChild(item);
        }
        if (study.non_ras_mutant_data) {
            hasRasData = true;
            const item = document.createElement('li');
            item.innerHTML = `<strong>Non-RAS-mutant:</strong> CR: ${study.non_ras_mutant_data.cr_rate || 'N/A'}%, OS: ${study.non_ras_mutant_data.os_median || 'N/A'} months (PMID: ${study.pmid})`;
            rasList.appendChild(item);
        }
    });

    if (hasRasData) {
        rasSection.appendChild(rasList);
    } else {
        const noData = document.createElement('p');
        noData.textContent = 'No specific RAS mutation subgroup data available.';
        rasSection.appendChild(noData);
    }
    card.appendChild(rasSection);

    // Serious Adverse Events
    const saeSection = document.createElement('div');
    saeSection.innerHTML = '<h3>Serious Adverse Events (SAEs)</h3>';
    const saeList = document.createElement('ul');
    
    const aggregateSAE = {};
    drugData.forEach(study => {
        if (study.sae_frequency !== null) {
            // For simplicity, we'll just average the SAE frequency if multiple studies report it
            // In a real dashboard, you might want to list individual SAEs or provide more detail
            if (!aggregateSAE['Overall SAE Frequency']) {
                aggregateSAE['Overall SAE Frequency'] = [];
            }
            aggregateSAE['Overall SAE Frequency'].push(study.sae_frequency);
        }
    });

    if (Object.keys(aggregateSAE).length > 0) {
        for (const saeType in aggregateSAE) {
            const item = document.createElement('li');
            item.textContent = `${saeType}: ${getAverage(aggregateSAE[saeType])}%`;
            saeList.appendChild(item);
        }
        saeSection.appendChild(saeList);
    } else {
        const noData = document.createElement('p');
        noData.textContent = 'No specific SAE frequency data available.';
        saeSection.appendChild(noData);
    }
    card.appendChild(saeSection);

    // Citations
    const citationsSection = document.createElement('div');
    citationsSection.innerHTML = '<h3>Citations</h3>';
    const citationsList = document.createElement('ul');
    const uniquePmids = new Set();

    drugData.forEach(study => {
        if (!uniquePmids.has(study.pmid)) {
            const item = document.createElement('li');
            item.innerHTML = `<a href="${study.url}" target="_blank">PMID: ${study.pmid}</a> - ${study.citation}`;
            citationsList.appendChild(item);
            uniquePmids.add(study.pmid);
        }
    });
    citationsSection.appendChild(citationsList);
    card.appendChild(citationsSection);

    return card;
}