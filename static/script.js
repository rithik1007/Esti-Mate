document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('estimateForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const jiraNumber = document.getElementById('jiraNumber').value;
        const description = document.getElementById('description').value;
        const useJira = document.getElementById('useJira').checked;
        const useAI = document.getElementById('useAI').checked;
        
        // Get selected phases
        const selectedPhases = {
            requirements: document.getElementById('includeRequirements').checked,
            design: document.getElementById('includeDesign').checked,
            development: document.getElementById('includeDevelopment').checked,
            testing: document.getElementById('includeTesting').checked,
            deployment: document.getElementById('includeDeployment').checked
        };
        
        if (useJira && !jiraNumber.trim()) {
            showErrorModal('Validation Error', 'Please enter a JIRA number when using JIRA fetch.');
            return;
        }
        
        if (!useJira && !description.trim()) {
            showErrorModal('Validation Error', 'Please enter a project description or use JIRA fetch.');
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
                    selected_phases: selectedPhases
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
    
    const phases = [];
    const hours = [];
    const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'];
    
    Object.entries(data.phases).forEach(([phase, phaseHours], index) => {
        const percentage = ((phaseHours / data.total_hours) * 100).toFixed(1);
        
        const row = tbody.insertRow();
        row.className = 'phase-row';
        row.innerHTML = `
            <td><strong>${phaseNames[phase]}</strong></td>
            <td>${phaseHours} hours</td>
            <td>${percentage}%</td>
        `;
        
        phases.push(phaseNames[phase]);
        hours.push(phaseHours);
    });
    
    // Create chart
    createChart(phases, hours, colors);
    
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