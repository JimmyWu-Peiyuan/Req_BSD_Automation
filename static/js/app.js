// Global state
let currentFile = null;
let analysisData = null;
let progressInterval = null;
let currentStages = [];

// DOM elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const clearFileBtn = document.getElementById('clearFile');
const analyzeBtn = document.getElementById('analyzeBtn');
const generateBtn = document.getElementById('generateBtn');

const uploadSection = document.getElementById('uploadSection');
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
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

clearFileBtn.addEventListener('click', () => {
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
            <p class="upload-hint">Supported formats: .xlsm, .xlsx</p>
        </div>
    `;
});

function handleFileSelect(file) {
    currentFile = file;
    fileName.textContent = file.name;
    fileInfo.style.display = 'flex';
    analyzeBtn.disabled = false;
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
            <p style="margin-bottom: 1rem; font-size: 1.1rem; color: var(--text-color);">
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
            displayResults(data);
        } else {
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
            
            updateProgress(data.progress, data.message, data.stage);
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

function updateProgress(progress, message, stage) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const progressMessage = document.getElementById('progressMessage');
    const progressStages = document.getElementById('progressStages');
    
    // Update progress bar
    progressFill.style.width = `${progress}%`;
    progressText.textContent = `${progress}%`;
    progressMessage.textContent = message;
    
    // Update stages
    updateStages(stage, progressStages);
}

function updateStages(currentStage, container) {
    const stages = [
        { id: 'initializing', label: 'Initializing LLM' },
        { id: 'bsd_overview', label: 'Generating Business Solution Overview' },
        { id: 'function_summary', label: 'Generating Function Summaries' },
        { id: 'function_implementation', label: 'Generating Function Implementations' },
        { id: 'document_assembly', label: 'Assembling Document' },
        { id: 'complete', label: 'Complete' }
    ];
    
    let html = '';
    let foundCurrent = false;
    
    stages.forEach((stage, index) => {
        const isCurrent = stage.id === currentStage && !foundCurrent;
        const isCompleted = foundCurrent || (currentStage === 'complete' && index < stages.length - 1);
        
        if (isCurrent) foundCurrent = true;
        
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
                        ⬇️ Download
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

