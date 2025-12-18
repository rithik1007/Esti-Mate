document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('estimateForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const jiraNumber = document.getElementById('jiraNumber').value.trim();
        const description = document.getElementById('description').value;
        const useAI = document.getElementById('useAI').checked;
        const usesAITools = document.getElementById('usesAITools').checked;
        
        // Auto-detect if JIRA should be used based on whether a JIRA number is provided
        const useJira = jiraNumber.length > 0;
        
        // Get selected phases with custom percentages
        const selectedPhases = {
            requirements: document.getElementById('includeRequirements').checked,
            design: document.getElementById('includeDesign').checked,
            development: document.getElementById('includeDevelopment').checked,
            testing: document.getElementById('includeTesting').checked,
            deployment: document.getElementById('includeDeployment').checked
        };
        
        const phasePercentages = {
            requirements: parseInt(document.getElementById('requirementsPercent').value) || 0,
            design: parseInt(document.getElementById('designPercent').value) || 0,
            development: parseInt(document.getElementById('developmentPercent').value) || 0,
            testing: parseInt(document.getElementById('testingPercent').value) || 0,
            deployment: parseInt(document.getElementById('deploymentPercent').value) || 0
        };
        
        // Get custom phases
        const customPhases = {};
        const customPhaseRows = document.querySelectorAll('.custom-phase-row');
        customPhaseRows.forEach((row, index) => {
            const checkbox = row.querySelector('input[type="checkbox"]');
            const nameInput = row.querySelector('.custom-phase-name');
            const percentInput = row.querySelector('.custom-phase-percent');
            
            if (checkbox.checked && nameInput.value.trim()) {
                const phaseName = nameInput.value.trim().toLowerCase().replace(/\s+/g, '_');
                selectedPhases[phaseName] = true;
                phasePercentages[phaseName] = parseInt(percentInput.value) || 0;
                customPhases[phaseName] = nameInput.value.trim();
                console.log(`DEBUG - Custom phase added: ${phaseName} = ${nameInput.value.trim()} (${percentInput.value}%)`);
            }
        });
        
        console.log('DEBUG - Final custom phases:', customPhases);
        console.log('DEBUG - Final selected phases:', selectedPhases);
        console.log('DEBUG - Final phase percentages:', phasePercentages);
        
        // Validate total percentage doesn't exceed 100%
        let totalPercent = 0;
        Object.values(phasePercentages).forEach(percent => {
            totalPercent += percent;
        });
        
        if (totalPercent > 100) {
            showErrorModal('Validation Error', 'Total phase percentages cannot exceed 100%. Current total: ' + totalPercent + '%');
            return;
        }
        
        if (!jiraNumber && !description.trim()) {
            showErrorModal('Validation Error', 'Please enter either a JIRA number or a project description.');
            return;
        }
        
        // Show loading
        loading.style.display = 'block';
        results.style.display = 'none';
        
        try {
            const response = await fetch('/estimate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jira_number: jiraNumber,
                    description: description,
                    use_jira: useJira,
                    use_ai: useAI,
                    uses_ai_tools: usesAITools,
                    selected_phases: selectedPhases,
                    phase_percentages: phasePercentages,
                    custom_phases: customPhases
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                displayResults(data);
            } else {
                const errorType = data.error_type || 'general';
                const errorTitle = getErrorTitle(errorType, response.status);
                showErrorModal(errorTitle, data.error || 'An error occurred');
                return;
            }
        } catch (error) {
            showErrorModal('Error', error.message);
        } finally {
            loading.style.display = 'none';
        }
    });
    
    // Add real-time percentage calculation
    const percentInputs = ['requirementsPercent', 'designPercent', 'developmentPercent', 'testingPercent', 'deploymentPercent'];
    
    percentInputs.forEach(inputId => {
        document.getElementById(inputId).addEventListener('input', updateTotalPercent);
    });
    
    // Add custom phase functionality
    let customPhaseCounter = 0;
    
    document.getElementById('addCustomPhase').addEventListener('click', function() {
        customPhaseCounter++;
        const customPhasesDiv = document.getElementById('customPhases');
        
        const phaseDiv = document.createElement('div');
        phaseDiv.className = 'row mb-2 custom-phase-row';
        phaseDiv.innerHTML = `
            <div class="col-md-6">
                <div class="d-flex align-items-center">
                    <input class="form-check-input me-2" type="checkbox" id="includeCustom${customPhaseCounter}" checked>
                    <input type="text" class="form-control form-control-sm me-2 custom-phase-name" 
                           id="customName${customPhaseCounter}" placeholder="Phase name" style="width: 120px;">
                    <input type="number" class="form-control form-control-sm custom-phase-percent" 
                           id="customPercent${customPhaseCounter}" value="0" min="0" max="100" style="width: 70px;">
                    <span class="ms-1 me-2">%</span>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-custom-phase">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        customPhasesDiv.appendChild(phaseDiv);
        
        // Add event listeners
        phaseDiv.querySelector('.custom-phase-percent').addEventListener('input', updateTotalPercent);
        phaseDiv.querySelector('.remove-custom-phase').addEventListener('click', function() {
            phaseDiv.remove();
            updateTotalPercent();
        });
        
        updateTotalPercent();
    });
    
    function updateTotalPercent() {
        let total = 0;
        percentInputs.forEach(inputId => {
            const value = parseInt(document.getElementById(inputId).value) || 0;
            total += value;
        });
        
        // Add custom phase percentages
        const customInputs = document.querySelectorAll('.custom-phase-percent');
        customInputs.forEach(input => {
            total += parseInt(input.value) || 0;
        });
        
        const totalSpan = document.getElementById('totalPercent');
        totalSpan.textContent = total;
        
        // Color coding for total
        if (total === 100) {
            totalSpan.className = 'fw-bold text-success';
        } else if (total > 100) {
            totalSpan.className = 'fw-bold text-danger';
        } else {
            totalSpan.className = 'fw-bold text-warning';
        }
    }
});

function getErrorTitle(errorType, statusCode) {
    switch (errorType) {
        case 'jira_error':
            if (statusCode === 400) {
                return 'JIRA Connection Issue';
            }
            return 'JIRA Error';
        default:
            return 'Error';
    }
}

function showErrorModal(title, message) {
    // Create modal if it doesn't exist
    let modal = document.getElementById('errorModal');
    if (!modal) {
        const modalHTML = `
            <div class="modal fade" id="errorModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title" id="errorModalTitle">Error</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="d-flex align-items-start">
                                <i class="bi bi-exclamation-triangle-fill text-danger me-3 fs-4"></i>
                                <p id="errorModalMessage" class="mb-0"></p>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        modal = document.getElementById('errorModal');
    }
    
    // Update modal content
    document.getElementById('errorModalTitle').textContent = title;
    document.getElementById('errorModalMessage').textContent = message;
    
    // Show modal
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
}

function displayResults(data) {
    // Clear any existing AI analysis and risk factor sections
    const existingAlerts = document.getElementById('results').querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Update basic info
    document.getElementById('resultJira').textContent = data.jira_number || 'N/A';
    document.getElementById('resultComplexity').textContent = data.complexity;
    document.getElementById('resultComplexity').className = `badge ${data.complexity}`;
    
    // Show estimation method and confidence
    let hoursText = data.total_hours + ' hours';
    if (data.estimation_method === 'ai_powered') {
        hoursText += ` <span class="badge bg-success ms-2"><i class="bi bi-robot"></i> AI: ${data.ai_confidence}% confident</span>`;
    } else {
        hoursText += ` <span class="badge bg-secondary ms-2">Rule-based</span>`;
    }
    document.getElementById('totalHours').innerHTML = hoursText;
    
    // Update JIRA details if available
    if (data.jira_details) {
        document.getElementById('resultIssueType').textContent = data.jira_details.issue_type;
        document.getElementById('resultPriority').textContent = data.jira_details.priority;
        document.getElementById('resultPriority').className = `badge priority-${data.jira_details.priority.toLowerCase()}`;
        document.getElementById('resultStatus').textContent = data.jira_details.status;
        document.getElementById('jiraDetailsRow').style.display = 'block';
    } else {
        document.getElementById('resultIssueType').textContent = 'Manual Entry';
        document.getElementById('jiraDetailsRow').style.display = 'none';
    }
    
    // Update phase breakdown table
    const tbody = document.getElementById('phaseBreakdown');
    tbody.innerHTML = '';
    
    const phaseNames = {
        'requirements': 'Requirements Gathering',
        'design': 'Design & Architecture',
        'development': 'Development & Coding',
        'testing': 'Testing & UAT',
        'deployment': 'Deployment & Production'
    };
    
    // Add custom phase names if available
    if (data.custom_phase_names) {
        Object.keys(data.custom_phase_names).forEach(key => {
            phaseNames[key] = data.custom_phase_names[key];
        });
    }
    
    // Add enterprise integration phase names
    const enterprisePhaseNames = {
        'iib_integration': 'IIB Integration',
        'sap_integration': 'SAP Integration', 
        'mainframe_integration': 'Mainframe Integration',
        'esb_integration': 'ESB Integration',
        'system_coordination': 'System Coordination'
    };
    Object.assign(phaseNames, enterprisePhaseNames);
    
    const phases = [];
    const hours = [];
    const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF', '#4BC0C0'];
    
    // Define the correct order for phases
    const phaseOrder = ['requirements', 'design', 'development', 'testing', 'deployment'];
    
    // Add any additional phases (enterprise integration, custom phases) after the standard ones
    const additionalPhases = Object.keys(data.phases).filter(phase => !phaseOrder.includes(phase));
    const orderedPhases = [...phaseOrder, ...additionalPhases];
    
    orderedPhases.forEach((phase, index) => {
        if (data.phases[phase] !== undefined && data.phases[phase] > 0) {
            const phaseHours = data.phases[phase];
            const percentage = ((phaseHours / data.total_hours) * 100).toFixed(1);
            
            // Get display name - use custom name if available, otherwise use default mapping, otherwise capitalize the phase key
            let displayName = phaseNames[phase];
            if (!displayName) {
                displayName = phase.charAt(0).toUpperCase() + phase.slice(1).replace(/_/g, ' ');
            }
            
            const row = tbody.insertRow();
            row.className = 'phase-row';
            
            // Check if this is testing phase and has breakdown
            if (phase === 'testing' && data.testing_breakdown && Object.keys(data.testing_breakdown).length > 0) {
                row.style.cursor = 'pointer';
                row.innerHTML = `
                    <td><strong>${displayName}</strong> <i class="bi bi-chevron-down" id="testingChevron"></i></td>
                    <td>${parseFloat(phaseHours).toFixed(2)} hours</td>
                    <td>${parseFloat(percentage).toFixed(1)}%</td>
                `;
                
                // Add click handler to expand/collapse
                row.onclick = function() {
                    toggleTestingBreakdown(data.testing_breakdown, phaseHours);
                };
            } else {
                row.innerHTML = `
                    <td><strong>${displayName}</strong></td>
                    <td>${parseFloat(phaseHours).toFixed(2)} hours</td>
                    <td>${parseFloat(percentage).toFixed(1)}%</td>
                `;
            }
            
            phases.push(displayName);
            hours.push(phaseHours);
        }
    });
    
    // Create chart
    createChart(phases, hours, colors);
    
    // Show JIRA timeline if available
    if (data.jira_details && data.jira_details.status_history) {
        displayJiraTimeline(data.jira_details.status_history, data.jira_details.time_in_status);
    }
    
    // Show historical comparison if available
    if (data.historical_analysis && data.historical_analysis.has_data) {
        displayHistoricalComparison(data.historical_analysis, data.phases, data.total_hours);
    }
    
    // Show risk factors if available
    if (data.risk_factors && data.risk_factors.length > 0) {
        const riskDiv = document.createElement('div');
        riskDiv.className = 'alert alert-warning mt-3';
        riskDiv.innerHTML = `
            <h6><i class="bi bi-exclamation-triangle"></i> Risk Factors:</h6>
            <ul class="mb-0">
                ${data.risk_factors.map(risk => `<li>${risk}</li>`).join('')}
            </ul>
        `;
        document.getElementById('results').appendChild(riskDiv);
    }
    
    // Show results
    document.getElementById('results').style.display = 'block';
    
    // Scroll to results
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}

function toggleTestingBreakdown(breakdown, totalTestingHours) {
    const tbody = document.getElementById('phaseBreakdown');
    const chevron = document.getElementById('testingChevron');
    const existingBreakdown = document.getElementById('testingBreakdownRow');
    
    // Toggle: if already expanded, collapse it
    if (existingBreakdown) {
        existingBreakdown.remove();
        if (chevron) {
            chevron.className = 'bi bi-chevron-down';
        }
        return;
    }
    
    // Change chevron to up
    if (chevron) {
        chevron.className = 'bi bi-chevron-up';
    }
    
    // Find the testing row
    const rows = tbody.getElementsByTagName('tr');
    let testingRowIndex = -1;
    for (let i = 0; i < rows.length; i++) {
        if (rows[i].textContent.includes('Testing & UAT')) {
            testingRowIndex = i;
            break;
        }
    }
    
    if (testingRowIndex === -1) return;
    
    // Define testing type descriptions
    const testingTypes = {
        'manual': {
            name: 'Manual Testing',
            icon: '👤',
            description: 'Exploratory testing, UI/UX validation'
        },
        'automation': {
            name: 'Automation Development',
            icon: '🤖',
            description: 'Writing automated test scripts'
        },
        'regression': {
            name: 'Regression Testing',
            icon: '🔄',
            description: 'Existing functionality validation'
        },
        'functional': {
            name: 'Functional Testing',
            icon: '✅',
            description: 'Feature validation, acceptance criteria'
        }
    };
    
    // Create breakdown content
    let breakdownHTML = '<td colspan="3" class="testing-breakdown-cell"><div class="testing-breakdown-content">';
    breakdownHTML += '<table class="table table-sm mb-0">';
    
    ['manual', 'automation', 'regression', 'functional'].forEach(type => {
        if (breakdown[type]) {
            const hours = breakdown[type];
            const percentage = totalTestingHours > 0 ? ((hours / totalTestingHours) * 100).toFixed(1) : 0;
            const typeInfo = testingTypes[type];
            
            breakdownHTML += `
                <tr>
                    <td style="width: 40%;"><span class="ms-3">${typeInfo.icon} ${typeInfo.name}</span></td>
                    <td style="width: 25%;"><span class="badge bg-info">${hours.toFixed(2)}h</span></td>
                    <td style="width: 35%;"><small class="text-muted">${typeInfo.description}</small></td>
                </tr>
            `;
        }
    });
    
    breakdownHTML += '</table></div></td>';
    
    // Insert breakdown row after testing row
    const breakdownRow = tbody.insertRow(testingRowIndex + 1);
    breakdownRow.id = 'testingBreakdownRow';
    breakdownRow.className = 'testing-breakdown-row';
    breakdownRow.innerHTML = breakdownHTML;
}

function displayJiraTimeline(statusHistory, timeInStatus) {
    const timelineDiv = document.getElementById('jiraTimeline');
    const tbody = document.getElementById('timelineBody');
    const totalCycleTimeSpan = document.getElementById('totalCycleTime');
    
    if (!timelineDiv || !tbody || !statusHistory || statusHistory.length === 0) {
        return;
    }
    
    tbody.innerHTML = '';
    let totalHours = 0;
    
    // Display each status transition
    statusHistory.forEach((transition, index) => {
        const fromStatus = transition.from || 'Created';
        const toStatus = transition.to;
        const date = new Date(transition.changed_at);
        const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        
        // Get time spent in the 'from' status
        const timeSpent = timeInStatus[fromStatus] || 0;
        totalHours += timeSpent;
        
        const row = tbody.insertRow();
        row.innerHTML = `
            <td><strong>${fromStatus}</strong> → ${toStatus}</td>
            <td><small>${dateStr}</small></td>
            <td><span class="badge bg-primary">${timeSpent.toFixed(1)}h</span></td>
        `;
    });
    
    // Add current status row
    if (statusHistory.length > 0) {
        const lastTransition = statusHistory[statusHistory.length - 1];
        const currentStatus = lastTransition.to;
        const timeInCurrent = timeInStatus[currentStatus] || 0;
        totalHours += timeInCurrent;
        
        const row = tbody.insertRow();
        row.className = 'table-success';
        row.innerHTML = `
            <td><strong>${currentStatus}</strong> (Current)</td>
            <td>-</td>
            <td><span class="badge bg-success">${timeInCurrent.toFixed(1)}h</span></td>
        `;
    }
    
    // Display total cycle time
    if (totalCycleTimeSpan) {
        totalCycleTimeSpan.innerHTML = `<strong>${totalHours.toFixed(1)} hours</strong> (${(totalHours / 8).toFixed(1)} days)`;
    }
    
    timelineDiv.style.display = 'block';
}

function displayHistoricalComparison(historical, estimatedPhases, totalEstimated) {
    const comparisonDiv = document.getElementById('historicalComparison');
    const tbody = document.getElementById('historicalBreakdown');
    const insightsList = document.getElementById('insightsList');
    
    if (!comparisonDiv || !tbody || !insightsList) {
        console.log('Historical comparison elements not found');
        return;
    }
    
    tbody.innerHTML = '';
    insightsList.innerHTML = '';
    
    // Map status time to phases
    const phaseMapping = {
        'requirements': historical.time_in_analysis || 0,
        'design': historical.time_in_analysis * 0.3 || 0,
        'development': historical.time_in_development || 0,
        'testing': historical.time_in_testing || 0,
        'deployment': 0
    };
    
    const actualLabels = [];
    const actualData = [];
    let hasActualData = false;
    
    // Create comparison rows
    ['requirements', 'design', 'development', 'testing', 'deployment'].forEach(phase => {
        const estimated = estimatedPhases[phase] || 0;
        const actual = phaseMapping[phase] || 0;
        
        if (estimated > 0 || actual > 0) {
            const variance = actual > 0 ? ((actual - estimated) / estimated * 100).toFixed(1) : 'N/A';
            const varianceClass = actual > estimated ? 'text-danger' : actual > 0 ? 'text-success' : '';
            const varianceIcon = actual > estimated ? '↑' : actual > 0 ? '↓' : '';
            
            const row = tbody.insertRow();
            row.innerHTML = `
                <td><strong>${phase.charAt(0).toUpperCase() + phase.slice(1)}</strong></td>
                <td>${estimated.toFixed(2)}h</td>
                <td>${actual > 0 ? actual.toFixed(2) + 'h' : '<span class="text-muted">Not started</span>'}</td>
                <td class="${varianceClass}">${variance !== 'N/A' ? varianceIcon + ' ' + Math.abs(variance) + '%' : variance}</td>
            `;
            
            if (actual > 0) {
                hasActualData = true;
                actualLabels.push(phase.charAt(0).toUpperCase() + phase.slice(1));
                actualData.push(actual);
            }
        }
    });
    
    // Add insights
    if (historical.patterns && historical.patterns.length > 0) {
        historical.patterns.forEach(pattern => {
            const li = document.createElement('li');
            li.textContent = pattern;
            insightsList.appendChild(li);
        });
    }
    
    // Add general insights
    if (historical.status_transitions > 0) {
        const li = document.createElement('li');
        li.textContent = `Ticket went through ${historical.status_transitions} status changes`;
        insightsList.appendChild(li);
    }
    
    if (historical.actual_time_spent > 0) {
        const li = document.createElement('li');
        li.textContent = `Total time logged in JIRA: ${historical.actual_time_spent.toFixed(1)} hours`;
        insightsList.appendChild(li);
    }
    
    if (historical.total_cycle_time > 0) {
        const li = document.createElement('li');
        li.textContent = `Total cycle time: ${historical.total_cycle_time.toFixed(1)} hours`;
        insightsList.appendChild(li);
    }
    
    // Show comparison section
    comparisonDiv.style.display = 'block';
    
    // Create actual time chart if data available
    if (hasActualData) {
        const actualContainer = document.getElementById('actualChartContainer');
        if (actualContainer) {
            actualContainer.style.display = 'block';
            createActualChart(actualLabels, actualData);
        }
    }
}

function createActualChart(labels, data) {
    const canvas = document.getElementById('actualChart');
    if (!canvas) {
        console.log('Actual chart canvas not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    if (window.actualChart && typeof window.actualChart.destroy === 'function') {
        window.actualChart.destroy();
    }
    
    const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'];
    
    window.actualChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value.toFixed(2)} hours (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function createChart(labels, data, colors) {
    const ctx = document.getElementById('estimateChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (window.estimateChart && typeof window.estimateChart.destroy === 'function') {
        window.estimateChart.destroy();
    }
    
    window.estimateChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} hours (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}