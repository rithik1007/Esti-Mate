// AI Workflow JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Design Generation Form
    document.getElementById('designForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const ticketKey = document.getElementById('ticketKey').value;
        const repoPath = document.getElementById('repoPath').value;
        const approvers = document.getElementById('approvers').value.split(',').map(a => a.trim());
        
        try {
            showLoading('Generating AI design...');
            
            const response = await fetch('/generate-design', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticket_key: ticketKey,
                    repo_path: repoPath,
                    approvers: approvers
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                displayDesignResults(data);
            } else {
                showError('Design Generation Error', data.error);
            }
        } catch (error) {
            showError('Network Error', error.message);
        } finally {
            hideLoading();
        }
    });
    
    // Code Generation Form
    document.getElementById('codeGenForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const approvalId = document.getElementById('codeApprovalId').value;
        const repoPath = document.getElementById('codeRepoPath').value;
        
        try {
            showLoading('Generating code snippets...');
            
            const response = await fetch('/generate-code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    approval_id: approvalId,
                    repo_path: repoPath
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                displayCodeResults(data);
            } else {
                showError('Code Generation Error', data.error);
            }
        } catch (error) {
            showError('Network Error', error.message);
        } finally {
            hideLoading();
        }
    });
    
    // Codebase Analysis Form
    document.getElementById('analyzeForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const repoPath = document.getElementById('analyzeRepoPath').value;
        
        try {
            showLoading('Analyzing codebase...');
            
            const response = await fetch('/analyze-codebase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_path: repoPath })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                displayAnalysisResults(data);
            } else {
                showError('Analysis Error', data.error);
            }
        } catch (error) {
            showError('Network Error', error.message);
        } finally {
            hideLoading();
        }
    });
    
    // Review Form
    document.getElementById('reviewForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const approvalId = document.getElementById('reviewApprovalId').value;
        const approver = document.getElementById('reviewerName').value;
        const comment = document.getElementById('reviewComment').value;
        const approved = document.querySelector('input[name=\"approvalDecision\"]:checked').value === 'true';
        
        try {
            const response = await fetch('/approve-design', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    approval_id: approvalId,
                    approver: approver,
                    comment: comment,
                    approved: approved
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showSuccess('Review Submitted', data.message);
                hideApprovalForm();
                loadPendingDesigns(); // Refresh the list
            } else {
                showError('Review Error', data.error);
            }
        } catch (error) {
            showError('Network Error', error.message);
        }
    });
});

function displayDesignResults(data) {
    const resultsDiv = document.getElementById('designResults');
    const contentDiv = document.getElementById('designContent');
    const approvalIdSpan = document.getElementById('approvalId');
    
    // Display design content
    let designHtml = '<div class=\"design-sections\">';
    
    if (data.design.solution_overview) {
        designHtml += `<div class=\"mb-3\"><strong>Solution Overview:</strong><br>${data.design.solution_overview}</div>`;
    }
    
    if (data.design.technical_architecture) {
        designHtml += `<div class=\"mb-3\"><strong>Technical Architecture:</strong><br>${data.design.technical_architecture}</div>`;
    }
    
    if (data.design.implementation_plan) {
        designHtml += `<div class=\"mb-3\"><strong>Implementation Plan:</strong><br>${data.design.implementation_plan}</div>`;
    }
    
    if (data.design.risk_assessment) {
        designHtml += `<div class=\"mb-3\"><strong>Risk Assessment:</strong><br>${data.design.risk_assessment}</div>`;
    }
    
    designHtml += '</div>';
    
    contentDiv.innerHTML = designHtml;
    approvalIdSpan.textContent = data.approval_id;
    resultsDiv.style.display = 'block';
}

function displayCodeResults(data) {
    const resultsDiv = document.getElementById('codeResults');
    const contentDiv = document.getElementById('codeContent');
    
    let codeHtml = '<div class=\"code-sections\">';
    
    const generatedCode = data.generated_code;
    
    // Backend Code
    if (generatedCode.backend_code && generatedCode.backend_code.code_blocks) {
        codeHtml += '<div class=\"mb-4\"><h6><i class=\"bi bi-server\"></i> Backend Code:</h6>';
        generatedCode.backend_code.code_blocks.forEach(block => {
            codeHtml += `
                <div class=\"mb-3\">
                    <div class=\"d-flex justify-content-between align-items-center bg-secondary text-white p-2\">
                        <span><strong>${block.filename || 'Code Block'}</strong></span>
                        <button class=\"btn btn-sm btn-outline-light\" onclick=\"copyToClipboard('${block.code.replace(/'/g, \"\\\\'\")}')\">
                            <i class=\"bi bi-clipboard\"></i> Copy
                        </button>
                    </div>
                    <pre class=\"bg-light p-3 border\"><code>${escapeHtml(block.code)}</code></pre>
                </div>
            `;
        });
        codeHtml += '</div>';
    }
    
    // Frontend Code
    if (generatedCode.frontend_code && generatedCode.frontend_code.code_blocks) {
        codeHtml += '<div class=\"mb-4\"><h6><i class=\"bi bi-display\"></i> Frontend Code:</h6>';
        generatedCode.frontend_code.code_blocks.forEach(block => {
            codeHtml += `
                <div class=\"mb-3\">
                    <div class=\"d-flex justify-content-between align-items-center bg-primary text-white p-2\">
                        <span><strong>${block.filename || 'Code Block'}</strong></span>
                        <button class=\"btn btn-sm btn-outline-light\" onclick=\"copyToClipboard('${block.code.replace(/'/g, \"\\\\'\")}')\">
                            <i class=\"bi bi-clipboard\"></i> Copy
                        </button>
                    </div>
                    <pre class=\"bg-light p-3 border\"><code>${escapeHtml(block.code)}</code></pre>
                </div>
            `;
        });
        codeHtml += '</div>';
    }
    
    // Test Code
    if (generatedCode.test_code && generatedCode.test_code.code_blocks) {
        codeHtml += '<div class=\"mb-4\"><h6><i class=\"bi bi-check-square\"></i> Test Code:</h6>';
        generatedCode.test_code.code_blocks.forEach(block => {
            codeHtml += `
                <div class=\"mb-3\">
                    <div class=\"d-flex justify-content-between align-items-center bg-success text-white p-2\">
                        <span><strong>${block.filename || 'Test Block'}</strong></span>
                        <button class=\"btn btn-sm btn-outline-light\" onclick=\"copyToClipboard('${block.code.replace(/'/g, \"\\\\'\")}')\">
                            <i class=\"bi bi-clipboard\"></i> Copy
                        </button>
                    </div>
                    <pre class=\"bg-light p-3 border\"><code>${escapeHtml(block.code)}</code></pre>
                </div>
            `;
        });
        codeHtml += '</div>';
    }
    
    codeHtml += '</div>';
    
    contentDiv.innerHTML = codeHtml;
    resultsDiv.style.display = 'block';
}

function displayAnalysisResults(data) {
    const resultsDiv = document.getElementById('analysisResults');
    const contentDiv = document.getElementById('analysisContent');
    
    const analysis = data.analysis;
    
    let analysisHtml = '<div class=\"analysis-sections\">';
    
    // Tech Stack
    if (analysis.tech_stack) {
        analysisHtml += `
            <div class=\"mb-4\">
                <h6><i class=\"bi bi-stack\"></i> Technology Stack:</h6>
                <div class=\"row\">
                    <div class=\"col-md-6\">
                        <strong>Languages:</strong> ${analysis.tech_stack.languages ? analysis.tech_stack.languages.join(', ') : 'Not detected'}
                    </div>
                    <div class=\"col-md-6\">
                        <strong>Frontend:</strong> ${analysis.tech_stack.frontend_framework || 'Not detected'}
                    </div>
                    <div class=\"col-md-6\">
                        <strong>Backend:</strong> ${analysis.tech_stack.backend_framework || 'Not detected'}
                    </div>
                    <div class=\"col-md-6\">
                        <strong>Testing:</strong> ${analysis.tech_stack.test_framework || 'Not detected'}
                    </div>
                </div>
            </div>
        `;
    }
    
    // Architecture Pattern
    if (analysis.architecture_pattern) {
        analysisHtml += `
            <div class=\"mb-4\">
                <h6><i class=\"bi bi-diagram-3\"></i> Architecture Pattern:</h6>
                <span class=\"badge bg-info\">${analysis.architecture_pattern}</span>
            </div>
        `;
    }
    
    // Code Patterns
    if (analysis.code_patterns) {
        analysisHtml += `
            <div class=\"mb-4\">
                <h6><i class=\"bi bi-code\"></i> Code Patterns:</h6>
                <div class=\"row\">
                    <div class=\"col-md-12\">
                        <strong>Naming Convention:</strong> ${analysis.code_patterns.naming_convention || 'Not detected'}
                    </div>
                </div>
            </div>
        `;
    }
    
    // Dependencies
    if (analysis.dependencies) {
        analysisHtml += `
            <div class=\"mb-4\">
                <h6><i class=\"bi bi-box\"></i> Dependencies:</h6>
                <div class=\"row\">
                    <div class=\"col-md-12\">
                        <strong>Package Manager:</strong> ${analysis.dependencies.package_manager || 'Not detected'}
                    </div>
                    <div class=\"col-md-12 mt-2\">
                        <strong>Key Dependencies:</strong><br>
                        ${analysis.dependencies.key_dependencies ? analysis.dependencies.key_dependencies.slice(0, 10).map(dep => `<span class=\"badge bg-secondary me-1\">${dep}</span>`).join('') : 'None detected'}
                    </div>
                </div>
            </div>
        `;
    }
    
    analysisHtml += '</div>';
    
    contentDiv.innerHTML = analysisHtml;
    resultsDiv.style.display = 'block';
}

async function loadPendingDesigns() {
    try {
        const response = await fetch('/pending-designs');
        const data = await response.json();
        
        const pendingDiv = document.getElementById('pendingDesigns');
        
        if (Object.keys(data.pending_designs).length === 0) {
            pendingDiv.innerHTML = '<p class=\"text-muted\">No pending designs found.</p>';
            return;
        }
        
        let html = '<div class=\"pending-designs-list\">';
        
        Object.entries(data.pending_designs).forEach(([approvalId, designData]) => {
            html += `
                <div class=\"card mb-3\">
                    <div class=\"card-header d-flex justify-content-between align-items-center\">
                        <span><strong>Ticket:</strong> ${designData.ticket_key}</span>
                        <span class=\"badge bg-warning\">Pending</span>
                    </div>
                    <div class=\"card-body\">
                        <p><strong>Approvers:</strong> ${designData.approvers.join(', ')}</p>
                        <p><strong>Submitted:</strong> ${designData.submitted_at}</p>
                        <button class=\"btn btn-primary btn-sm\" onclick=\"showApprovalForm('${approvalId}')\">
                            <i class=\"bi bi-eye\"></i> Review Design
                        </button>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        pendingDiv.innerHTML = html;
        
    } catch (error) {
        showError('Load Error', 'Failed to load pending designs');
    }
}

function showApprovalForm(approvalId) {
    document.getElementById('reviewApprovalId').value = approvalId;
    document.getElementById('approvalForm').style.display = 'block';
}

function hideApprovalForm() {
    document.getElementById('approvalForm').style.display = 'none';
    document.getElementById('reviewForm').reset();
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showSuccess('Copied!', 'Code copied to clipboard');
    }).catch(() => {
        showError('Copy Failed', 'Failed to copy to clipboard');
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading(message) {
    // Create or show loading indicator
    let loading = document.getElementById('globalLoading');
    if (!loading) {
        loading = document.createElement('div');
        loading.id = 'globalLoading';
        loading.className = 'position-fixed top-50 start-50 translate-middle bg-white p-4 rounded shadow';
        loading.style.zIndex = '9999';
        loading.innerHTML = `
            <div class=\"text-center\">
                <div class=\"spinner-border text-primary\" role=\"status\"></div>
                <p class=\"mt-2 mb-0\">${message}</p>
            </div>
        `;
        document.body.appendChild(loading);
    } else {
        loading.querySelector('p').textContent = message;
        loading.style.display = 'block';
    }
}

function hideLoading() {
    const loading = document.getElementById('globalLoading');
    if (loading) {
        loading.style.display = 'none';
    }
}

function showSuccess(title, message) {
    showNotification(title, message, 'success');
}

function showError(title, message) {
    showNotification(title, message, 'danger');
}

function showNotification(title, message, type) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.innerHTML = `
        <strong>${title}:</strong> ${message}
        <button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"alert\"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}