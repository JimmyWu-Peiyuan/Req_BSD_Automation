// Global state
let currentFile = null;
let analysisData = null;
let progressInterval = null;
let functionList = []; // Store list of functions for checklist
let completedStages = new Set(); // Track completed stages

// DOM elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const clearFileBtn = document.getElementById('clearFile');
const analyzeBtn = document.getElementById('analyzeBtn');
const generateBtn = document.getElementById('generateBtn');

const analysisSection = document.getElementById('analysisSection');
const progressSection = document.getElementById('progressSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');

// File upload handling
uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        const ext = file.name.split('.').pop().toLowerCase();
        if (['xlsm', 'xlsx', 'csv'].includes(ext)) {
            handleFileSelect(file);
        } else {
            alert('Unsupported file format. Please upload .xlsm, .xlsx, or .csv');
        }
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        const file = e.target.files[0];
        const ext = file.name.split('.').pop().toLowerCase();
        if (['xlsm', 'xlsx', 'csv'].includes(ext)) {
            handleFileSelect(file);
        } else {
            alert('Unsupported file format. Please upload .xlsm, .xlsx, or .csv');
        }
    }
});

clearFileBtn.addEventListener('click', () => {
    resetUI(true); // Reset everything including file
});

function handleFileSelect(file) {
    resetUI(false); // Reset UI but keep results
    currentFile = file;
    fileName.textContent = file.name;
    fileInfo.style.display = 'flex';
    analyzeBtn.disabled = false;
}

function resetUI(clearFile = false) {
    // Stop progress polling
    stopProgressPolling();
    
    // Reset state
    completedStages.clear();
    functionList = [];
    
    // Hide sections (except results)
    analysisSection.style.display = 'none';
    progressSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    // Reset progress bar
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const progressMessage = document.getElementById('progressMessage');
    const progressStages = document.getElementById('progressStages');
    
    if (progressFill) progressFill.style.width = '0%';
    if (progressText) progressText.textContent = '0%';
    if (progressMessage) progressMessage.textContent = '';
    if (progressStages) {
        progressStages.style.display = 'block';
        progressStages.innerHTML = '';
    }
    
    // Clear analysis data
    analysisData = null;
    
    // Clear file if requested
    if (clearFile) {
        currentFile = null;
        fileInput.value = '';
        fileInfo.style.display = 'none';
        analyzeBtn.disabled = true;
        uploadArea.innerHTML = `
            <div class="upload-content">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="17 8 12 3 7 8"></polyline>
                    <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
                <p class="upload-text">Click to select file or drag and drop</p>
                <p class="upload-hint">Supported formats: .xlsm, .xlsx, .csv</p>
            </div>
        `;
    }
}

// Analyze requirements
analyzeBtn.addEventListener('click', async () => {
    if (!currentFile) return;
    
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';
    hideError();
    
    const formData = new FormData();
    formData.append('file', currentFile);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Upload failed');
        }
        
        analysisData = data;
        displayAnalysis(data);
        analysisSection.style.display = 'block';
        
    } catch (error) {
        showError(error.message);
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze Requirements';
    }
});

function displayAnalysis(data) {
    const content = document.getElementById('analysisContent');
    
    let html = `
        <div class="bsd-summary">
            <p style="margin-bottom: 16px; font-size: 1.1rem; color: #1E2A4A;">
                Found <strong>${data.bsd_count}</strong> BSD(s) to generate
            </p>
    `;
    
    data.bsd_groups.forEach(bsd => {
        html += `
            <div class="bsd-item">
                <h3>BSD #${bsd.bsd_number}: ${bsd.bsd_id}</h3>
                <p><strong>Product:</strong> ${bsd.sales_product}</p>
                <p><strong>Domain:</strong> ${bsd.domain}</p>
                <p><strong>Requirements:</strong> ${bsd.requirement_count}</p>
                <p><strong>Functions:</strong> ${bsd.unique_functions.length}</p>
            </div>
        `;
    });
    
    html += '</div>';
    content.innerHTML = html;
}

// Generate documents
generateBtn.addEventListener('click', async () => {
    if (!analysisData) return;
    
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';
    hideError();
    
    // Show progress section
    progressSection.style.display = 'block';
    resultsSection.style.display = 'none';
    
    // Start polling for progress
    startProgressPolling();
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Generation failed');
        }
        
        if (data.success) {
            stopProgressPolling();
            // Mark all stages as completed
            completedStages.add('initializing');
            completedStages.add('bsd_overview');
            functionList.forEach(func => {
                completedStages.add(`function_summary_${func}`);
                completedStages.add(`function_implementation_${func}`);
            });
            completedStages.add('document_assembly');
            // Ensure progress shows 100% and hide checklist
            updateProgress(100, 'All documents generated successfully!', 'complete', functionList);
            displayResults(data);
        } else {
            stopProgressPolling();
            throw new Error(data.error || 'Generation failed');
        }
        
    } catch (error) {
        stopProgressPolling();
        showError(error.message);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate BSD Documents';
    }
});

// Progress polling
function startProgressPolling() {
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/progress');
            const data = await response.json();
            
            // Update function list if provided
            if (data.functions && data.functions.length > 0) {
                functionList = data.functions;
            }
            
            updateProgress(data.progress, data.message, data.stage, data.functions || []);
            
            // Stop polling when complete
            if (data.progress >= 100 || data.stage === 'complete') {
                stopProgressPolling();
            }
        } catch (error) {
            console.error('Error fetching progress:', error);
        }
    }, 500); // Poll every 500ms
}

function stopProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

function updateProgress(progress, message, stage, functions = []) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const progressMessage = document.getElementById('progressMessage');
    const progressStages = document.getElementById('progressStages');
    
    // Update progress bar
    progressFill.style.width = `${progress}%`;
    progressText.textContent = `${progress}%`;
    progressMessage.textContent = message;
    
    // Track completed stages
    if (stage && !stage.startsWith('function_')) {
        // Mark previous stages as completed when moving to next major stage
        if (stage === 'bsd_overview') {
            completedStages.add('initializing');
        } else if (stage === 'document_assembly') {
            completedStages.add('bsd_overview');
            // Mark all function stages as completed
            functions.forEach(func => {
                completedStages.add(`function_summary_${func}`);
                completedStages.add(`function_implementation_${func}`);
            });
        } else if (stage === 'complete') {
            completedStages.add('document_assembly');
        }
    } else if (stage && stage.startsWith('function_')) {
        // Mark function stages as completed when moving to next
        const parts = stage.split('_');
        if (parts.length >= 3 && functions.length > 0) {
            const funcName = parts.slice(2).join('_');
            const currentIndex = functions.indexOf(funcName);
            
            if (currentIndex >= 0) {
                if (stage.startsWith('function_summary_')) {
                    completedStages.add('bsd_overview');
                    // Mark all previous function stages as completed
                    for (let i = 0; i < currentIndex; i++) {
                        completedStages.add(`function_summary_${functions[i]}`);
                        completedStages.add(`function_implementation_${functions[i]}`);
                    }
                } else if (stage.startsWith('function_implementation_')) {
                    // Mark the corresponding summary as completed
                    completedStages.add(`function_summary_${funcName}`);
                    // Mark all previous function stages as completed (including implementations)
                    for (let i = 0; i < currentIndex; i++) {
                        completedStages.add(`function_summary_${functions[i]}`);
                        completedStages.add(`function_implementation_${functions[i]}`);
                    }
                }
            }
        }
    }
    
    // Hide checklist when progress reaches 100%
    if (progress >= 100 || stage === 'complete') {
        progressStages.style.display = 'none';
    } else {
        progressStages.style.display = 'block';
        // Update stages with function list
        updateStages(stage, progressStages, message, functions);
    }
}

function updateStages(currentStage, container, message = '', functions = []) {
    // Build stages dynamically
    const stages = [
        { id: 'initializing', label: 'Initializing LLM' },
        { id: 'bsd_overview', label: 'Generating Business Solution Overview' }
    ];
    
    // Add function-specific stages
    functions.forEach((funcName, index) => {
        stages.push({
            id: `function_summary_${funcName}`,
            label: `Summary: ${funcName}`,
            functionName: funcName,
            type: 'summary'
        });
        stages.push({
            id: `function_implementation_${funcName}`,
            label: `Implementation: ${funcName}`,
            functionName: funcName,
            type: 'implementation'
        });
    });
    
    stages.push({ id: 'document_assembly', label: 'Assembling Document' });
    stages.push({ id: 'complete', label: 'Complete' });
    
    let html = '';
    
    stages.forEach((stage) => {
        const isCurrent = stage.id === currentStage;
        const isCompleted = completedStages.has(stage.id);
        
        html += `
            <div class="stage-item ${isCurrent ? 'active' : ''} ${isCompleted ? 'completed' : ''}">
                <div class="stage-icon">
                    ${isCompleted ? '<span class="completed">✓</span>' : isCurrent ? '<div class="spinner"></div>' : ''}
                </div>
                <div class="stage-text">${stage.label}</div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function displayResults(data) {
    const content = document.getElementById('resultsContent');
    
    let html = `
        <table class="results-table">
            <thead>
                <tr>
                    <th>BSD Number</th>
                    <th>BSD ID</th>
                    <th>Filename</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    data.documents.forEach(doc => {
        html += `
            <tr>
                <td>${doc.bsd_number}</td>
                <td>${doc.bsd_id}</td>
                <td>${doc.filename}</td>
                <td>
                    <a href="/api/download/${doc.filename}" class="download-btn" download>
                        Download
                    </a>
                </td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    content.innerHTML = html;
    resultsSection.style.display = 'block';
}

function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
}

function hideError() {
    errorSection.style.display = 'none';
}

