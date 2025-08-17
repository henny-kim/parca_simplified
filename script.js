document.addEventListener('DOMContentLoaded', () => {
    // Add cache busting to prevent browser caching
    const timestamp = new Date().getTime();
    
    fetch(`data/cmml_detailed_outcomes.json?t=${timestamp}`)
        .then(response => response.json())
        .then(data => {
            populateSummary(data.extraction_metadata);
            populateDetailedAnalysis(data);
            populateComparativeAnalysis(data);
        });

    fetch(`summarized_outcomes.json?t=${timestamp}`)
        .then(response => response.json())
        .then(data => {
            populateSummarizedOutcomes(data);
        });

    const navLinks = document.querySelectorAll('.nav a');
    const sections = document.querySelectorAll('.content-section');

    navLinks.forEach(link => {
        link.addEventListener('click', e => {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            const targetId = link.getAttribute('href').substring(1);
            sections.forEach(section => {
                if (section.id === targetId) {
                    section.style.display = 'block';
                } else {
                    section.style.display = 'none';
                }
            });
        });
    });

    // Initially show the summary section
    document.getElementById('summary').style.display = 'block';
    document.getElementById('summarized-outcomes').style.display = 'none';
    document.getElementById('detailed-analysis').style.display = 'none';
    document.getElementById('comparative-analysis').style.display = 'none';
});

function populateSummary(metadata) {
    const summaryContent = document.getElementById('summary-content');
    summaryContent.innerHTML = `
        <div class="summary-card">
            <h3>Total Papers Processed</h3>
            <p>${metadata.total_papers_processed}</p>
        </div>
        <div class="summary-card">
            <h3>Extraction Date</h3>
            <p>${new Date(metadata.extraction_date).toLocaleDateString()}</p>
        </div>
    `;
}

function populateSummarizedOutcomes(data) {
    const summarizedOutcomesContent = document.getElementById('summarized-outcomes-content');
    summarizedOutcomesContent.innerHTML = '';

    for (const drug in data) {
        const drugData = data[drug];
        const table = document.createElement('table');
        table.className = 'drug-table';
        table.innerHTML = `
            <caption>${drug.replace(/_/g, ' ').toUpperCase()}</caption>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Mean</th>
                    <th>Median</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Complete Response (CR)</td>
                    <td>${drugData.efficacy.cr_mean?.toFixed(2) || 'N/A'}</td>
                    <td>${drugData.efficacy.cr_median?.toFixed(2) || 'N/A'}</td>
                </tr>
                <tr>
                    <td>Overall Response Rate (ORR)</td>
                    <td>${drugData.efficacy.orr_mean?.toFixed(2) || 'N/A'}</td>
                    <td>${drugData.efficacy.orr_median?.toFixed(2) || 'N/A'}</td>
                </tr>
                <tr>
                    <td>Progression-Free Survival (PFS)</td>
                    <td>${drugData.survival.pfs_mean?.toFixed(2) || 'N/A'}</td>
                    <td>${drugData.survival.pfs_median?.toFixed(2) || 'N/A'}</td>
                </tr>
                <tr>
                    <td>Overall Survival (OS)</td>
                    <td>${drugData.survival.os_mean?.toFixed(2) || 'N/A'}</td>
                    <td>${drugData.survival.os_median?.toFixed(2) || 'N/A'}</td>
                </tr>
                <tr>
                    <td>Serious Adverse Events (SAE)</td>
                    <td>${drugData.safety?.sae_mean?.toFixed(2) || 'N/A'}</td>
                    <td>${drugData.safety?.sae_median?.toFixed(2) || 'N/A'}</td>
                </tr>
            </tbody>
        `;
        summarizedOutcomesContent.appendChild(table);
    }
}

function populateDetailedAnalysis(data) {
    const detailedAnalysisContent = document.getElementById('detailed-analysis-content');
    detailedAnalysisContent.innerHTML = '';

    for (const drug in data) {
        if (drug === 'extraction_metadata') continue;

        const drugStudies = data[drug];
        const table = document.createElement('table');
        table.className = 'drug-table';
        table.innerHTML = `
            <caption>${drug.charAt(0).toUpperCase() + drug.slice(1)}</caption>
            <thead>
                <tr>
                    <th>Citation</th>
                    <th>Key Findings</th>
                    <th>Study Design</th>
                    <th>Patient Population</th>
                    <th>Treatment Details</th>
                </tr>
            </thead>
            <tbody>
                ${drugStudies.map(study => `
                    <tr>
                        <td><a href="${study.url}" target="_blank">${study.citation}</a></td>
                        <td>${study.key_findings}</td>
                        <td>${study.study_design}</td>
                        <td>${study.patient_population}</td>
                        <td>${study.treatment_details}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        detailedAnalysisContent.appendChild(table);
    }
}

function populateComparativeAnalysis(data) {
    const drugs = Object.keys(data).filter(key => key !== 'extraction_metadata');
    const crData = {
        labels: [],
        datasets: [{
            label: 'Complete Response Rate (%)',
            data: [],
            backgroundColor: 'rgba(26, 115, 232, 0.7)',
        }]
    };
    const osData = {
        labels: [],
        datasets: [{
            label: 'Median Overall Survival (months)',
            data: [],
            backgroundColor: 'rgba(217, 48, 37, 0.7)',
        }]
    };

    drugs.forEach(drug => {
        const studies = data[drug];
        const avgCR = studies.reduce((acc, study) => acc + (study.complete_response || 0), 0) / studies.length;
        const avgOS = studies.reduce((acc, study) => acc + (study.os_median || 0), 0) / studies.length;

        crData.labels.push(drug);
        crData.datasets[0].data.push(avgCR.toFixed(2));

        osData.labels.push(drug);
        osData.datasets[0].data.push(avgOS.toFixed(2));
    });

    const crChartCtx = document.getElementById('cr-chart').getContext('2d');
    new Chart(crChartCtx, {
        type: 'bar',
        data: crData,
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                title: { display: true, text: 'Average Complete Response Rate by Drug' }
            }
        }
    });

    const osChartCtx = document.getElementById('os-chart').getContext('2d');
    new Chart(osChartCtx, {
        type: 'bar',
        data: osData,
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                title: { display: true, text: 'Average Median Overall Survival by Drug' }
            }
        }
    });
}

// Load section-specific content
function loadSectionContent(sectionName) {
    if (!dashboardData) return;
    
    switch (sectionName) {
        case 'overview':
            loadOverviewSection();
            break;
        case 'summaries':
            loadSummariesSection();
            break;
        case 'efficacy':
            loadEfficacySection();
            break;
        case 'ras-analysis':
            loadRASAnalysisSection();
            break;
        case 'safety':
            loadSafetySection();
            break;
        case 'studies':
            loadStudiesSection();
            break;
        case 'paper-details':
            loadPaperDetailsSection();
            break;
    }
}

// Paper Details Section
function loadPaperDetailsSection() {
    const section = document.getElementById('paper-details');
    if (!section) return;
    
    const paperDetailsList = section.querySelector('.paper-details-list');
    const drugFilter = section.querySelector('#paperDrugFilter');
    const dataTypeFilter = section.querySelector('#dataTypeFilter');
    
    displayPaperDetails(paperDetailsList, 'all', 'all');
    
    drugFilter.addEventListener('change', (e) => {
        displayPaperDetails(paperDetailsList, e.target.value, dataTypeFilter.value);
    });
    
    dataTypeFilter.addEventListener('change', (e) => {
        displayPaperDetails(paperDetailsList, drugFilter.value, e.target.value);
    });
}

function displayPaperDetails(container, selectedDrug, selectedDataType) {
    container.innerHTML = '';
    
    const drugs = ['azacitidine', 'decitabine', 'hydroxyurea'];
    const papersToShow = selectedDrug === 'all' ? drugs : [selectedDrug];
    
    let totalPapers = 0;
    let papersWithData = 0;
    
    papersToShow.forEach(drug => {
        if (dashboardData[drug]) {
            const drugPapers = dashboardData[drug];
            totalPapers += drugPapers.length;
            
            drugPapers.forEach(paper => {
                const hasRelevantData = checkDataRelevance(paper, selectedDataType);
                if (hasRelevantData) {
                    papersWithData++;
                    const paperCard = createPaperCard(paper, drug);
                    container.appendChild(paperCard);
                }
            });
        }
    });
    
    if (papersWithData === 0) {
        container.innerHTML = `
            <div class="no-data-message">
                <h3>No papers found</h3>
                <p>No papers match the selected criteria.</p>
                <p>Total papers analyzed: ${totalPapers}</p>
            </div>
        `;
    } else {
        // Add summary at the top
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'summary-info';
        summaryDiv.innerHTML = `
            <div class="data-highlight">
                Showing ${papersWithData} papers with ${selectedDataType === 'all' ? 'any' : selectedDataType} data 
                from ${selectedDrug === 'all' ? 'all drugs' : selectedDrug}
            </div>
        `;
        container.insertBefore(summaryDiv, container.firstChild);
    }
}

function checkDataRelevance(paper, dataType) {
    if (dataType === 'all') return true;
    
    switch (dataType) {
        case 'efficacy':
            return paper.complete_response !== null || 
                   paper.partial_response !== null || 
                   paper.marrow_complete_response !== null || 
                   paper.marrow_optimal_response !== null;
        case 'safety':
            return paper.sae_frequency !== null;
        case 'survival':
            return paper.pfs_median !== null || 
                   paper.os_median !== null || 
                   paper.efs_median !== null;
        case 'ras':
            return (paper.ras_mutant_data && Object.values(paper.ras_mutant_data).some(v => v !== null)) ||
                   (paper.non_ras_mutant_data && Object.values(paper.non_ras_mutant_data).some(v => v !== null));
        default:
            return true;
    }
}

function createPaperCard(paper, drugName) {
    const card = document.createElement('div');
    card.className = 'paper-card';
    
    // Header with title, drug badge, and metadata
    const header = document.createElement('div');
    header.className = 'paper-header';
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'paper-title';
    titleDiv.innerHTML = `
        <h4>${paper.citation.split('.')[0]}</h4>
        <div class="paper-meta">
            <strong>PMID:</strong> ${paper.pmid}<br>
            <strong>Study Design:</strong> ${paper.study_design || 'Not specified'}<br>
            <strong>Sample Size:</strong> ${paper.cmml_sample_size || 'Not specified'} CMML patients
        </div>
    `;
    
    const drugBadge = document.createElement('div');
    drugBadge.className = 'paper-drug-badge';
    drugBadge.textContent = drugName.charAt(0).toUpperCase() + drugName.slice(1);
    
    header.appendChild(titleDiv);
    header.appendChild(drugBadge);
    
    // Data grid showing extracted information
    const dataGrid = document.createElement('div');
    dataGrid.className = 'paper-data-grid';
    
    // Efficacy data
    const efficacyData = createDataCategory('Efficacy Data', {
        'Complete Response': paper.complete_response,
        'Partial Response': paper.partial_response,
        'Marrow Complete Response': paper.marrow_complete_response,
        'Marrow Optimal Response': paper.marrow_optimal_response
    });
    
    // Safety data
    const safetyData = createDataCategory('Safety Data', {
        'SAE Frequency': paper.sae_frequency
    });
    
    // Survival data
    const survivalData = createDataCategory('Survival Data', {
        'PFS Median': paper.pfs_median,
        'OS Median': paper.os_median,
        'EFS Median': paper.efs_median
    });
    
    // RAS mutation data
    const rasData = createDataCategory('RAS Mutation Data', {
        'RAS-Mutant CR Rate': paper.ras_mutant_data?.cr_rate,
        'RAS-Mutant OS Median': paper.ras_mutant_data?.os_median,
        'Non-RAS-Mutant CR Rate': paper.non_ras_mutant_data?.cr_rate,
        'Non-RAS-Mutant OS Median': paper.non_ras_mutant_data?.os_median
    });
    
    dataGrid.appendChild(efficacyData);
    dataGrid.appendChild(safetyData);
    dataGrid.appendChild(survivalData);
    dataGrid.appendChild(rasData);
    
    // Supporting quotes
    let quotesSection = '';
    if (paper.supporting_quotes && paper.supporting_quotes.length > 0) {
        quotesSection = `
            <div class="paper-quotes">
                <h5>Supporting Quotes</h5>
                ${paper.supporting_quotes.map(quote => 
                    `<div class="quote-item">"${quote}"</div>`
                ).join('')}
            </div>
        `;
    }
    
    // Key findings
    let findingsSection = '';
    if (paper.key_findings) {
        findingsSection = `
            <div class="paper-quotes">
                <h5>Key Findings</h5>
                <div class="quote-item">${paper.key_findings}</div>
            </div>
        `;
    }
    
    // Links
    const linksSection = `
        <div class="paper-links">
            <a href="${paper.url}" target="_blank">View on PubMed</a>
            <a href="https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}/" target="_blank">PMID: ${paper.pmid}</a>
        </div>
    `;
    
    card.innerHTML = `
        ${header.outerHTML}
        ${dataGrid.outerHTML}
        ${findingsSection}
        ${quotesSection}
        ${linksSection}
    `;

    return card;
}

function createDataCategory(title, data) {
    const category = document.createElement('div');
    category.className = 'data-category';
    
    const titleElem = document.createElement('h5');
    titleElem.textContent = title;
    category.appendChild(titleElem);
    
    Object.entries(data).forEach(([label, value]) => {
        const dataItem = document.createElement('div');
        dataItem.className = 'data-item';
        
        const labelElem = document.createElement('span');
        labelElem.className = 'data-label';
        labelElem.textContent = label;
        
        const valueElem = document.createElement('span');
        valueElem.className = 'data-value';
        if (value === null || value === undefined) {
            valueElem.textContent = 'Not reported';
            valueElem.classList.add('null');
        } else {
            if (typeof value === 'number') {
                if (label.includes('Response') || label.includes('Rate') || label.includes('Frequency')) {
                    valueElem.textContent = `${value}%`;
                } else if (label.includes('Median')) {
                    valueElem.textContent = `${value} months`;
                } else {
                    valueElem.textContent = value;
                }
            } else {
                valueElem.textContent = value;
            }
        }
        
        dataItem.appendChild(labelElem);
        dataItem.appendChild(valueElem);
        category.appendChild(dataItem);
    });
    
    return category;
}