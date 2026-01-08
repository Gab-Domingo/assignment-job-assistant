// ===== Global State =====
let uploadedProfile = null;
let selectedFile = null;
let workflowFile = null;

const API_BASE_URL = 'http://localhost:8000';

// ===== Tab Management =====
function showTab(tabName) {
    // Hide all tab panels
    const panels = document.querySelectorAll('.tab-panel');
    panels.forEach(panel => panel.classList.remove('active'));
    
    // Remove active from all buttons
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
}

// ===== File Upload Handling =====
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        selectedFile = file;
        showFileSelected('uploadArea', file.name);
        document.getElementById('uploadBtn').disabled = false;
    }
}

function handleWorkflowFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        workflowFile = file;
        showFileSelected('workflowUploadArea', file.name);
    }
}

function showFileSelected(areaId, fileName) {
    const area = document.getElementById(areaId);
    let selectedDiv = area.querySelector('.file-selected');
    
    if (!selectedDiv) {
        selectedDiv = document.createElement('div');
        selectedDiv.className = 'file-selected';
        area.appendChild(selectedDiv);
    }
    
    selectedDiv.textContent = `✓ Selected: ${fileName}`;
}

// Drag and drop support
document.addEventListener('DOMContentLoaded', () => {
    const uploadAreas = document.querySelectorAll('.file-upload-area');
    
    uploadAreas.forEach(area => {
        area.addEventListener('dragover', (e) => {
            e.preventDefault();
            area.classList.add('drag-over');
        });
        
        area.addEventListener('dragleave', () => {
            area.classList.remove('drag-over');
        });
        
        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.classList.remove('drag-over');
            
            const file = e.dataTransfer.files[0];
            const input = area.querySelector('input[type="file"]');
            
            if (file && input) {
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                input.files = dataTransfer.files;
                
                if (input.id === 'resumeFile') {
                    handleFileSelect({ target: input });
                } else if (input.id === 'workflowResumeFile') {
                    handleWorkflowFileSelect({ target: input });
                }
            }
        });
    });
});

// ===== Profile Source Toggle =====
function toggleProfileSource() {
    const source = document.querySelector('input[name="profileSource"]:checked').value;
    const manualSection = document.getElementById('manualProfileSection');
    
    if (source === 'manual') {
        manualSection.style.display = 'block';
    } else {
        manualSection.style.display = 'none';
    }
}

// ===== API Calls =====

// Show/hide loading overlay
function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

// Upload Resume
async function uploadResume() {
    if (!selectedFile) {
        showAlert('uploadResult', 'Please select a file first', 'error');
        return;
    }
    
    const detailed = document.getElementById('detailedUpload').checked;
    const endpoint = detailed ? '/upload_resume_detailed' : '/upload_resume';
    
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (detailed) {
                uploadedProfile = data.profile;
                displayDetailedUploadResult(data);
            } else {
                uploadedProfile = data;
                displaySimpleUploadResult(data);
            }
        } else {
            showAlert('uploadResult', `Error: ${data.detail || 'Upload failed'}`, 'error');
        }
    } catch (error) {
        showAlert('uploadResult', `Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displaySimpleUploadResult(profile) {
    const resultDiv = document.getElementById('uploadResult');
    const contentDiv = document.getElementById('uploadResultContent');
    
    contentDiv.innerHTML = `
        <div class="result-card">
            <h4>Personal Information</h4>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Name</div>
                    <div class="info-value">${profile.personal_info.full_name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Email</div>
                    <div class="info-value">${profile.personal_info.email}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Location</div>
                    <div class="info-value">${profile.personal_info.location}</div>
                </div>
            </div>
            <p><strong>Summary:</strong> ${profile.personal_info.professional_summary}</p>
        </div>
        
        <div class="result-card">
            <h4>Profile Overview</h4>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Work Experience</div>
                    <div class="info-value">${profile.work_history?.length || 0} positions</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Education</div>
                    <div class="info-value">${profile.education?.length || 0} entries</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Projects</div>
                    <div class="info-value">${profile.projects?.length || 0} projects</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Technical Skills</div>
                    <div class="info-value">${profile.skills?.technical?.length || 0} skills</div>
                </div>
            </div>
        </div>
        
        <div class="alert alert-success">
            ✓ Profile extracted successfully! You can now use this profile in other tabs.
        </div>
    `;
    
    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function displayDetailedUploadResult(data) {
    const resultDiv = document.getElementById('uploadResult');
    const contentDiv = document.getElementById('uploadResultContent');
    
    const profile = data.profile;
    const confidence = (data.ocr_confidence * 100).toFixed(1);
    const confidenceClass = confidence >= 90 ? 'high' : confidence >= 70 ? 'medium' : 'low';
    
    contentDiv.innerHTML = `
        <div class="result-card">
            <h4>OCR Quality Metrics</h4>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Confidence Score</div>
                    <div class="info-value match-score ${confidenceClass}">${confidence}%</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Pages Processed</div>
                    <div class="info-value">${data.extraction_metadata.pages_processed}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Text Length</div>
                    <div class="info-value">${data.extraction_metadata.raw_text_length} chars</div>
                </div>
            </div>
        </div>
        
        <div class="result-card">
            <h4>Extracted Profile</h4>
            <p><strong>${profile.personal_info.full_name}</strong></p>
            <p>${profile.personal_info.email} • ${profile.personal_info.location}</p>
            <p style="margin-top: 1rem;">${profile.personal_info.professional_summary}</p>
            
            <div style="margin-top: 1.5rem;">
                <div class="metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">Work History:</span>
                        <span class="metadata-value">${profile.work_history?.length || 0}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Education:</span>
                        <span class="metadata-value">${profile.education?.length || 0}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Projects:</span>
                        <span class="metadata-value">${profile.projects?.length || 0}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Skills:</span>
                        <span class="metadata-value">${profile.skills?.technical?.length || 0}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="alert alert-success">
            ✓ Resume processed successfully! Profile saved and ready to use.
        </div>
    `;
    
    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Analyze Job Match
async function analyzeJob() {
    const profileSource = document.querySelector('input[name="profileSource"]:checked').value;
    let profile;
    
    if (profileSource === 'upload') {
        if (!uploadedProfile) {
            showAlert('analyzeResult', 'Please upload a resume first in the Upload Resume tab', 'warning');
            return;
        }
        profile = uploadedProfile;
    } else {
        const manualProfile = document.getElementById('manualProfile').value;
        if (!manualProfile) {
            showAlert('analyzeResult', 'Please enter a profile JSON', 'error');
            return;
        }
        try {
            profile = JSON.parse(manualProfile);
        } catch (e) {
            showAlert('analyzeResult', 'Invalid JSON format', 'error');
            return;
        }
    }
    
    const jobTitle = document.getElementById('jobTitle').value;
    const jobLocation = document.getElementById('jobLocation').value;
    const jobUrl = document.getElementById('jobUrl').value;
    
    if (!jobUrl && (!jobTitle || !jobLocation)) {
        showAlert('analyzeResult', 'Please provide either a job URL or both job title and location', 'warning');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_profile: profile,
                job_params: {
                    job_title: jobTitle || null,
                    location: jobLocation || null,
                    url: jobUrl || null
                }
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayAnalysisResult(data);
        } else {
            showAlert('analyzeResult', `Error: ${data.detail || 'Analysis failed'}`, 'error');
        }
    } catch (error) {
        showAlert('analyzeResult', `Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayAnalysisResult(analysis) {
    const resultDiv = document.getElementById('analyzeResult');
    const contentDiv = document.getElementById('analyzeResultContent');
    
    const scoreClass = analysis.match_score >= 75 ? 'high' : analysis.match_score >= 50 ? 'medium' : 'low';
    
    contentDiv.innerHTML = `
        <div class="result-card">
            <h4>Match Score</h4>
            <div style="text-align: center; margin: 1.5rem 0;">
                <div class="match-score ${scoreClass}">${analysis.match_score}/100</div>
            </div>
        </div>
        
        <div class="result-card">
            <div class="list-section">
                <h5>✓ Key Matches</h5>
                <ul>
                    ${analysis.key_matches.map(match => `<li>${match}</li>`).join('')}
                </ul>
            </div>
        </div>
        
        ${analysis.gaps && analysis.gaps.length > 0 ? `
        <div class="result-card">
            <div class="list-section">
                <h5>⚠️ Areas for Improvement</h5>
                <ul>
                    ${analysis.gaps.map(gap => `<li>${gap}</li>`).join('')}
                </ul>
            </div>
        </div>
        ` : ''}
        
        <div class="result-card">
            <div class="list-section">
                <h5>💡 Suggestions</h5>
                <ul>
                    ${analysis.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
    
    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Generate Answer
async function generateAnswer() {
    const profileSource = document.querySelector('input[name="profileSourceGen"]:checked').value;
    let profile;
    
    if (profileSource === 'upload') {
        if (!uploadedProfile) {
            showAlert('generateResult', 'Please upload a resume first in the Upload Resume tab', 'warning');
            return;
        }
        profile = uploadedProfile;
    } else {
        showAlert('generateResult', 'Manual profile entry not implemented yet. Please use uploaded resume.', 'warning');
        return;
    }
    
    const jobTitle = document.getElementById('jobTitleGen').value;
    const jobLocation = document.getElementById('jobLocationGen').value;
    const questionText = document.getElementById('questionText').value;
    const questionType = document.getElementById('questionType').value;
    const maxLength = parseInt(document.getElementById('maxLength').value);
    
    if (!jobTitle || !jobLocation) {
        showAlert('generateResult', 'Please provide job title and location', 'warning');
        return;
    }
    
    if (!questionText) {
        showAlert('generateResult', 'Please enter an application question', 'warning');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/generate_answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_profile: profile,
                job_params: {
                    job_title: jobTitle,
                    location: jobLocation
                },
                application_question: {
                    question_id: 'q1',
                    question_text: questionText,
                    question_type: questionType,
                    max_length: maxLength
                }
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayGeneratedAnswer(data);
        } else {
            showAlert('generateResult', `Error: ${data.detail || 'Generation failed'}`, 'error');
        }
    } catch (error) {
        showAlert('generateResult', `Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayGeneratedAnswer(data) {
    const resultDiv = document.getElementById('generateResult');
    const contentDiv = document.getElementById('generateResultContent');
    
    const answer = data.final_answer;
    
    contentDiv.innerHTML = `
        <div class="result-card">
            <h4>Generated Answer</h4>
            <div class="answer-box">
                ${answer.text}
            </div>
            <div class="metadata">
                <div class="metadata-item">
                    <span class="metadata-label">Word Count:</span>
                    <span class="metadata-value">${answer.word_count}</span>
                </div>
            </div>
        </div>
        
        <div class="result-card">
            <div class="list-section">
                <h5>Key Points Addressed</h5>
                <ul>
                    ${answer.key_points_addressed.map(point => `<li>${point}</li>`).join('')}
                </ul>
            </div>
        </div>
        
        ${answer.tailored_elements.skills_mentioned.length > 0 ? `
        <div class="result-card">
            <h4>Tailored Elements</h4>
            <p><strong>Skills Mentioned:</strong> ${answer.tailored_elements.skills_mentioned.join(', ')}</p>
            ${answer.tailored_elements.experience_highlighted.length > 0 ? 
                `<p><strong>Experience Highlighted:</strong> ${answer.tailored_elements.experience_highlighted.join(', ')}</p>` : ''}
        </div>
        ` : ''}
        
        <div class="alert alert-success">
            ✓ Answer generated successfully! You can copy and customize it for your application.
        </div>
    `;
    
    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Complete Workflow
async function runCompleteWorkflow() {
    if (!workflowFile) {
        showAlert('workflowResult', 'Please select a resume file', 'warning');
        return;
    }
    
    const jobTitle = document.getElementById('workflowJobTitle').value;
    const jobLocation = document.getElementById('workflowJobLocation').value;
    const question = document.getElementById('workflowQuestion').value;
    
    if (!jobTitle || !jobLocation || !question) {
        showAlert('workflowResult', 'Please fill in all fields', 'warning');
        return;
    }
    
    const progressDiv = document.getElementById('workflowProgress');
    const resultDiv = document.getElementById('workflowResult');
    progressDiv.style.display = 'block';
    resultDiv.style.display = 'none';
    
    try {
        // Step 1: Upload resume
        updateProgressStep('step1', 'active', '⏳');
        const formData = new FormData();
        formData.append('file', workflowFile);
        
        const uploadResponse = await fetch(`${API_BASE_URL}/upload_resume`, {
            method: 'POST',
            body: formData
        });
        
        if (!uploadResponse.ok) {
            throw new Error('Resume upload failed');
        }
        
        const profile = await uploadResponse.json();
        updateProgressStep('step1', 'completed', '✓');
        
        // Step 2: Analyze job match
        updateProgressStep('step2', 'active', '⏳');
        const analyzeResponse = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_profile: profile,
                job_params: { job_title: jobTitle, location: jobLocation }
            })
        });
        
        if (!analyzeResponse.ok) {
            throw new Error('Job analysis failed');
        }
        
        const analysis = await analyzeResponse.json();
        updateProgressStep('step2', 'completed', '✓');
        
        // Step 3: Generate answer
        updateProgressStep('step3', 'active', '⏳');
        const generateResponse = await fetch(`${API_BASE_URL}/generate_answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_profile: profile,
                job_params: { job_title: jobTitle, location: jobLocation },
                application_question: {
                    question_id: 'wq1',
                    question_text: question,
                    question_type: 'essay',
                    max_length: 500
                }
            })
        });
        
        if (!generateResponse.ok) {
            throw new Error('Answer generation failed');
        }
        
        const answerData = await generateResponse.json();
        updateProgressStep('step3', 'completed', '✓');
        
        // Display complete results
        displayWorkflowResults(profile, analysis, answerData);
        
    } catch (error) {
        const activeStep = document.querySelector('.progress-step.active');
        if (activeStep) {
            updateProgressStep(activeStep.id, 'error', '✗');
        }
        showAlert('workflowResult', `Error: ${error.message}`, 'error');
    }
}

function updateProgressStep(stepId, status, icon) {
    const step = document.getElementById(stepId);
    step.className = `progress-step ${status}`;
    step.querySelector('.step-icon').textContent = icon;
}

function displayWorkflowResults(profile, analysis, answerData) {
    const resultDiv = document.getElementById('workflowResult');
    const contentDiv = document.getElementById('workflowResultContent');
    
    const answer = answerData.final_answer;
    const scoreClass = analysis.match_score >= 75 ? 'high' : analysis.match_score >= 50 ? 'medium' : 'low';
    
    contentDiv.innerHTML = `
        <div class="result-card">
            <h4>📄 Extracted Profile</h4>
            <p><strong>${profile.personal_info.full_name}</strong></p>
            <p>${profile.personal_info.email} • ${profile.personal_info.location}</p>
        </div>
        
        <div class="result-card">
            <h4>📊 Job Match Analysis</h4>
            <div style="text-align: center; margin: 1rem 0;">
                <div class="match-score ${scoreClass}">${analysis.match_score}/100</div>
            </div>
            <div class="list-section">
                <h5>Top Matches:</h5>
                <ul>
                    ${analysis.key_matches.slice(0, 3).map(match => `<li>${match}</li>`).join('')}
                </ul>
            </div>
        </div>
        
        <div class="result-card">
            <h4>✍️ Generated Answer</h4>
            <div class="answer-box">
                ${answer.text}
            </div>
            <div class="metadata">
                <div class="metadata-item">
                    <span class="metadata-label">Word Count:</span>
                    <span class="metadata-value">${answer.word_count}</span>
                </div>
            </div>
        </div>
        
        <div class="alert alert-success">
            🎉 Workflow completed successfully! Your application materials are ready.
        </div>
    `;
    
    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Utility Functions
function showAlert(containerId, message, type = 'info') {
    const container = document.getElementById(containerId);
    const alertClass = type === 'error' ? 'alert-error' : 
                       type === 'warning' ? 'alert-warning' : 
                       type === 'success' ? 'alert-success' : 'alert-info';
    
    container.innerHTML = `<div class="alert ${alertClass}">${message}</div>`;
    container.style.display = 'block';
    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

