// ===== Global State =====
let candidates = [];
let selectedFile = null;
let selectedBatchFiles = [];

// Shortlisting state
let shortlistQueue = [];
let currentShortlistIndex = 0;
let shortlistedCandidates = [];
let currentJobTitle = null; // Shared job title from Analyze tab

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
    
    // Load data when switching to certain tabs
    if (tabName === 'candidates') {
        loadCandidates();
    } else if (tabName === 'analyze') {
        populateCandidateDropdown();
        loadAvailableProfiles(); // Always load ideal profiles when tab is shown
    } else if (tabName === 'shortlist') {
        // Reset shortlisting state when tab is opened
        shortlistQueue = [];
        currentShortlistIndex = 0;
        shortlistedCandidates = [];
        // Update job title display
        updateShortlistingJobTitleDisplay();
    } else if (tabName === 'analytics') {
        populateCandidateCheckboxes();
    }
}

// ===== Upload Mode Toggle =====
function toggleUploadMode() {
    const mode = document.querySelector('input[name="uploadMode"]:checked').value;
    const singleSection = document.getElementById('singleUploadSection');
    const batchSection = document.getElementById('batchUploadSection');
    
    if (mode === 'single') {
        singleSection.style.display = 'block';
        batchSection.style.display = 'none';
    } else {
        singleSection.style.display = 'none';
        batchSection.style.display = 'block';
    }
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

function handleBatchFileSelect(event) {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
        selectedBatchFiles = files;
        showFileSelected('batchUploadArea', `${files.length} file(s) selected`);
        document.getElementById('batchUploadBtn').disabled = false;
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
            
            const files = e.dataTransfer.files;
            const input = area.querySelector('input[type="file"]');
            
            if (files && input) {
                const dataTransfer = new DataTransfer();
                for (let file of files) {
                    dataTransfer.items.add(file);
                }
                input.files = dataTransfer.files;
                
                if (input.id === 'resumeFile') {
                    handleFileSelect({ target: input });
                } else if (input.id === 'batchResumeFiles') {
                    handleBatchFileSelect({ target: input });
                }
            }
        });
    });
});

// ===== API Calls =====

function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

// Upload Single Resume
async function uploadResume() {
    if (!selectedFile) {
        showAlert('uploadResult', 'Please select a file first', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        const response = await fetch(`${API_BASE_URL}/api/candidates/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            candidates.push(data);
            displayUploadResult(data, 1, 0);
        } else {
            showAlert('uploadResult', `Error: ${data.detail || 'Upload failed'}`, 'error');
        }
    } catch (error) {
        showAlert('uploadResult', `Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

// Batch Upload Resumes
async function batchUploadResumes() {
    if (!selectedBatchFiles || selectedBatchFiles.length === 0) {
        showAlert('uploadResult', 'Please select files first', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const formData = new FormData();
        selectedBatchFiles.forEach(file => {
            formData.append('files', file);
        });
        
        const response = await fetch(`${API_BASE_URL}/api/candidates/batch-upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            candidates.push(...data.candidates);
            displayUploadResult(data, data.successful, data.failed);
        } else {
            showAlert('uploadResult', `Error: ${data.detail || 'Upload failed'}`, 'error');
        }
    } catch (error) {
        showAlert('uploadResult', `Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayUploadResult(data, successful, failed) {
    const resultDiv = document.getElementById('uploadResult');
    const contentDiv = document.getElementById('uploadResultContent');
    
    let html = '';
    
    if (successful > 1 || (data.candidates && data.candidates.length > 1)) {
        // Batch upload result
        html = `
            <div class="alert alert-success">
                ✓ Successfully uploaded ${successful} candidate(s)${failed > 0 ? `, ${failed} failed` : ''}
            </div>
            <div class="result-card">
                <h4>Uploaded Candidates</h4>
                <ul>
                    ${(data.candidates || [data]).map(c => `
                        <li><strong>ID:</strong> ${c.id}<br>
                        <strong>Name:</strong> ${c.profile_data?.personal_info?.full_name || 'N/A'}<br>
                        <strong>File:</strong> ${c.resume_filename || 'N/A'}</li>
                    `).join('')}
                </ul>
            </div>
        `;
    } else {
        // Single upload result
        const candidate = data.candidates ? data.candidates[0] : data;
        const profile = candidate.profile_data;
        html = `
            <div class="alert alert-success">
                ✓ Candidate uploaded successfully! ID: ${candidate.id}
            </div>
            <div class="result-card">
                <h4>Candidate Information</h4>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Candidate ID</div>
                        <div class="info-value">${candidate.id}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Name</div>
                        <div class="info-value">${profile?.personal_info?.full_name || 'N/A'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Email</div>
                        <div class="info-value">${profile?.personal_info?.email || 'N/A'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Location</div>
                        <div class="info-value">${profile?.personal_info?.location || 'N/A'}</div>
                    </div>
                    ${candidate.ocr_confidence ? `
                    <div class="info-item">
                        <div class="info-label">OCR Confidence</div>
                        <div class="info-value">${(candidate.ocr_confidence * 100).toFixed(1)}%</div>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    contentDiv.innerHTML = html;
    resultDiv.style.display = 'block';
}

// Load Candidates List
async function loadCandidates() {
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/candidates`);
        const data = await response.json();
        
        if (response.ok) {
            candidates = data;
            displayCandidates(data);
        } else {
            showAlert('candidatesList', `Error: ${data.detail || 'Failed to load candidates'}`, 'error');
        }
    } catch (error) {
        showAlert('candidatesList', `Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayCandidates(candidatesList) {
    const container = document.getElementById('candidatesList');
    const emptyState = document.getElementById('candidatesEmpty');
    
    if (!candidatesList || candidatesList.length === 0) {
        container.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    container.style.display = 'grid';
    emptyState.style.display = 'none';
    
    container.innerHTML = candidatesList.map(candidate => {
        const profile = candidate.profile_data || {};
        const personalInfo = profile.personal_info || {};
        const skills = profile.skills?.technical || [];
        
        return `
            <div class="candidate-card">
                <h4>${personalInfo.full_name || 'Unknown'}</h4>
                <div class="candidate-info">
                    <p><strong>Email:</strong> ${personalInfo.email || 'N/A'}</p>
                    <p><strong>Location:</strong> ${personalInfo.location || 'N/A'}</p>
                    <p><strong>ID:</strong> <code>${candidate.id}</code></p>
                    <p><strong>Skills:</strong> ${skills.length} technical skills</p>
                    ${candidate.resume_filename ? `<p><strong>Resume:</strong> ${candidate.resume_filename}</p>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// Populate Candidate Dropdown
async function populateCandidateDropdown() {
    const select = document.getElementById('candidateSelect');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/candidates`);
        const data = await response.json();
        
        select.innerHTML = '<option value="">-- Select a candidate --</option>' +
            data.map(c => {
                const name = c.profile_data?.personal_info?.full_name || 'Unknown';
                return `<option value="${c.id}">${name} (${c.id})</option>`;
            }).join('');
    } catch (error) {
        console.error('Failed to load candidates:', error);
    }
}

// Load Candidate Details (for analyze tab)
async function loadCandidateDetails() {
    const candidateId = document.getElementById('candidateSelect').value;
    // Could show preview of candidate info here if needed
}

// Analyze Candidate (using RAG) - Shows confirmation message
async function analyzeCandidate() {
    const candidateId = document.getElementById('candidateSelect').value;
    const jobTitle = document.getElementById('jobTitle').value;
    const jobLocation = document.getElementById('jobLocation').value;
    
    if (!candidateId) {
        showAlert('analyzeResult', 'Please select a candidate', 'warning');
        return;
    }
    
    if (!jobTitle) {
        showAlert('analyzeResult', 'Please provide a job title', 'warning');
        return;
    }
    
    // Show loading
    showLoading();
    
    try {
        // RAG is enabled by default, pass use_rag=true explicitly
        const url = new URL(`${API_BASE_URL}/api/candidates/${candidateId}/analyze`);
        url.searchParams.append('job_title', jobTitle);
        if (jobLocation) url.searchParams.append('job_location', jobLocation);
        url.searchParams.append('use_rag', 'true');
        
        const response = await fetch(url, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store job title for shortlisting tab
            storeJobTitleForShortlisting(jobTitle);
            // Show confirmation message instead of full results
            displayAnalysisConfirmation(data, jobTitle);
        } else {
            showAlert('analyzeResult', `Error: ${data.detail || 'Analysis failed'}`, 'error');
        }
    } catch (error) {
        const resultDiv = document.getElementById('analyzeResult');
        const contentDiv = document.getElementById('analyzeResultContent');
        
        if (resultDiv && contentDiv) {
            contentDiv.innerHTML = `
                <div class="alert alert-error">
                    Error: ${error.message}
                </div>
            `;
            resultDiv.style.display = 'block';
        } else {
            showAlert('analyzeResult', `Error: ${error.message}`, 'error');
        }
    } finally {
        hideLoading();
    }
}

// Store job title when analyzing (for use in Shortlisting tab)
function storeJobTitleForShortlisting(jobTitle) {
    currentJobTitle = jobTitle;
    updateShortlistingJobTitleDisplay();
}

function updateShortlistingJobTitleDisplay() {
    const displayEl = document.getElementById('currentJobTitleDisplay');
    const hintEl = document.getElementById('shortlistJobTitleHint');
    const loadBtn = document.getElementById('loadShortlistBtn');
    
    if (displayEl) {
        if (currentJobTitle) {
            displayEl.textContent = currentJobTitle;
            displayEl.style.color = 'var(--success-color)';
            if (hintEl) hintEl.style.display = 'none';
            if (loadBtn) loadBtn.disabled = false;
        } else {
            displayEl.textContent = 'Not set - Please select a job title in the Analyze Candidate tab first';
            displayEl.style.color = 'var(--text-secondary)';
            if (hintEl) hintEl.style.display = 'block';
            if (loadBtn) loadBtn.disabled = true;
        }
    }
}

// Display analysis confirmation message
function displayAnalysisConfirmation(analysis, jobTitle) {
    const resultDiv = document.getElementById('analyzeResult');
    const contentDiv = document.getElementById('analyzeResultContent');
    
    if (!resultDiv || !contentDiv) {
        console.error('Result divs not found');
        return;
    }
    
    const scoreClass = analysis.match_score >= 75 ? 'high' : analysis.match_score >= 50 ? 'medium' : 'low';
    const scoreLabel = analysis.match_score >= 75 ? 'Excellent Match' : analysis.match_score >= 50 ? 'Good Match' : 'Needs Improvement';
    
    contentDiv.innerHTML = `
        <div class="result-card">
            <h4>✅ Analysis Complete</h4>
            <div style="text-align: center; margin: 1.5rem 0;">
                <div class="match-score ${scoreClass}">${analysis.match_score}/100</div>
                <p style="margin-top: 0.5rem; font-weight: 600; color: var(--text-primary);">${scoreLabel}</p>
            </div>
            <p style="text-align: center; color: #666; margin-top: 1rem;">
                Candidate has been analyzed against <strong>${jobTitle}</strong> ideal profile.
            </p>
            <p style="text-align: center; color: #27ae60; font-size: 0.9rem; margin-top: 0.5rem;">
                🤖 Powered by RAG (Vector Database Matching)
            </p>
        </div>
        
        <div class="result-card">
            <h5>Quick Summary</h5>
            <div style="margin-top: 1rem;">
                <p><strong>Key Matches:</strong> ${(analysis.key_matches || []).length} identified</p>
                <p><strong>Skill Gaps:</strong> ${(analysis.gaps || []).length} areas for improvement</p>
                <p><strong>Suggestions:</strong> ${(analysis.suggestions || []).length} recommendations provided</p>
            </div>
        </div>
    `;
    
    resultDiv.style.display = 'block';
    // Scroll to result
    resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Load available ideal profiles (always shown)
async function loadAvailableProfiles() {
    const listDiv = document.getElementById('idealProfilesList');
    
    if (!listDiv) {
        console.error('idealProfilesList element not found');
        return;
    }
    
    // Show loading state
    listDiv.innerHTML = '<p style="color: #666;">Loading ideal profiles...</p>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/ideal-profiles`);
        const data = await response.json();
        
        if (response.ok) {
            displayIdealProfiles(data);
        } else {
            listDiv.innerHTML = `<div class="alert alert-warning">Error: ${data.detail || 'Failed to load profiles'}</div>`;
        }
    } catch (error) {
        listDiv.innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
    }
}

function displayIdealProfiles(data) {
    const listDiv = document.getElementById('idealProfilesList');
    
    if (!listDiv) {
        console.error('idealProfilesList element not found');
        return;
    }
    
    const profiles = data.profiles || [];
    const stats = data.stats || {};
    
    if (profiles.length === 0) {
        listDiv.innerHTML = '<p style="color: #666;">No ideal profiles available. Profiles are loaded from ChromaDB.</p>';
    } else {
        listDiv.innerHTML = `
            <p style="margin-bottom: 1rem; color: #666;">📊 <strong>${stats.profile_count || profiles.length}</strong> ideal profiles available</p>
            <div class="ideal-profiles-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 0.75rem; margin-top: 0.5rem;">
                ${profiles.map(p => {
                    const profile = p.profile || {};
                    return `
                        <div class="ideal-profile-card" style="background: #f8f9fa; padding: 0.75rem; border-radius: 8px; border: 1px solid #e0e0e0;">
                            <div style="font-weight: bold; color: #2c3e50; margin-bottom: 0.25rem;">${profile.job_title || 'N/A'}</div>
                            <div style="font-size: 0.85rem; color: #666;">
                                ${profile.years_experience ? `${profile.years_experience} yrs exp` : ''}
                                ${profile.must_have_skills && profile.must_have_skills.length ? ` • ${profile.must_have_skills.length} must-have skills` : ''}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }
}

// This function is kept for backward compatibility but displayAnalysisConfirmation is used instead
function displayAnalysisResult(analysis) {
    displayAnalysisConfirmation(analysis, analysis.job_title || 'Unknown');
}

// ===== Analytics Sub-tabs =====
function showAnalyticsSubTab(subtab) {
    const subtabs = document.querySelectorAll('.analytics-subtab');
    subtabs.forEach(t => t.classList.remove('active'));
    document.getElementById(`${subtab}-subtab`).classList.add('active');
    
    const buttons = document.querySelectorAll('#analytics-tab .subtab-button');
    buttons.forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
}

function showMarketSubTab(subtab) {
    const subtabs = document.querySelectorAll('.market-subtab');
    subtabs.forEach(t => t.classList.remove('active'));
    document.getElementById(`${subtab}-subtab`).classList.add('active');
    
    const buttons = document.querySelectorAll('#market-tab .subtab-button');
    buttons.forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
}

// Populate Candidate Checkboxes for Comparison
async function populateCandidateCheckboxes() {
    const container = document.getElementById('candidateCheckboxes');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/candidates`);
        const data = await response.json();
        
        container.innerHTML = data.map(c => {
            const name = c.profile_data?.personal_info?.full_name || 'Unknown';
            return `
                <label>
                    <input type="checkbox" name="compareCandidates" value="${c.id}">
                    ${name} (${c.id.substring(0, 8)}...)
                </label>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load candidates:', error);
    }
}

// Compare Candidates
async function compareCandidates() {
    const checkboxes = document.querySelectorAll('input[name="compareCandidates"]:checked');
    const candidateIds = Array.from(checkboxes).map(cb => cb.value);
    
    if (candidateIds.length < 2) {
        showAlert('compareResult', 'Please select at least 2 candidates to compare', 'warning');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/analytics/comparison?candidate_ids=${candidateIds.join(',')}`);
        const data = await response.json();
        
        if (response.ok) {
            displayComparisonResult(data);
        } else {
            showAlert('compareResult', `Error: ${data.detail || 'Comparison failed'}`, 'error');
        }
    } catch (error) {
        showAlert('compareResult', `Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayComparisonResult(data) {
    const resultDiv = document.getElementById('compareResult');
    const contentDiv = document.getElementById('compareResultContent');
    
    const skillsComparison = data.skills_comparison || {};
    const skills = Object.keys(skillsComparison);
    
    let skillsMatrixHtml = '';
    if (skills.length > 0) {
        skillsMatrixHtml = `
            <div class="result-card">
                <h4>Skills Comparison Matrix</h4>
                <div class="comparison-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Skill</th>
                                ${data.candidates.map(c => `<th>${c.name}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${skills.map(skill => `
                                <tr>
                                    <td><strong>${skill}</strong></td>
                                    ${data.candidates.map(c => {
                                        const hasSkill = skillsComparison[skill]?.[c.id] || false;
                                        return `<td>${hasSkill ? '✓' : '✗'}</td>`;
                                    }).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    contentDiv.innerHTML = `
        <div class="result-card">
            <h4>Candidates Being Compared</h4>
            <div class="info-grid">
                ${data.candidates.map(c => `
                    <div class="info-item">
                        <div class="info-label">${c.name}</div>
                        <div class="info-value">${c.skills_count} skills</div>
                    </div>
                `).join('')}
            </div>
        </div>
        ${skillsMatrixHtml}
    `;
    
    resultDiv.style.display = 'block';
}

// Skills Gap Analysis
async function loadSkillsGap() {
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/analytics/skills-gap`);
        const data = await response.json();
        
        if (response.ok) {
            displaySkillsGap(data);
        } else {
            showAlert('skillsGapResult', `Error: ${data.detail || 'Failed to load skills gap'}`, 'error');
        }
    } catch (error) {
        showAlert('skillsGapResult', `Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displaySkillsGap(data) {
    const resultDiv = document.getElementById('skillsGapResult');
    const contentDiv = document.getElementById('skillsGapResultContent');
    
    if (data.message) {
        contentDiv.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
    } else {
        const skillCoverage = data.skill_coverage || {};
        const skills = Object.entries(skillCoverage).sort((a, b) => b[1].count - a[1].count);
        
        contentDiv.innerHTML = `
            <div class="result-card">
                <h4>Skills Gap Analysis</h4>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Total Candidates</div>
                        <div class="info-value">${data.total_candidates}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Unique Skills</div>
                        <div class="info-value">${data.unique_skills}</div>
                    </div>
                </div>
            </div>
            <div class="result-card">
                <h4>Skill Coverage</h4>
                ${skills.map(([skill, info]) => `
                    <div style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                            <span><strong>${skill}</strong></span>
                            <span>${info.count}/${data.total_candidates} (${info.percentage.toFixed(1)}%)</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${info.percentage}%"></div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    resultDiv.style.display = 'block';
}

// Statistics
async function loadStatistics() {
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/analytics/statistics`);
        const data = await response.json();
        
        if (response.ok) {
            displayStatistics(data);
        } else {
            showAlert('statisticsResult', `Error: ${data.detail || 'Failed to load statistics'}`, 'error');
        }
    } catch (error) {
        showAlert('statisticsResult', `Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayStatistics(data) {
    const resultDiv = document.getElementById('statisticsResult');
    const contentDiv = document.getElementById('statisticsResultContent');
    
    contentDiv.innerHTML = `
        <div class="result-card">
            <h4>Overall Statistics</h4>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Total Candidates</div>
                    <div class="info-value">${data.total_candidates || 0}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Total Analyses</div>
                    <div class="info-value">${data.total_analyses || 0}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Average Match Score</div>
                    <div class="info-value">${data.average_match_score || 0}</div>
                </div>
            </div>
        </div>
        ${data.top_skills && data.top_skills.length > 0 ? `
        <div class="result-card">
            <h4>Top Skills</h4>
            <ul>
                ${data.top_skills.map(s => `<li><strong>${s.skill}</strong> - ${s.count} candidate(s)</li>`).join('')}
            </ul>
        </div>
        ` : ''}
    `;
    
    resultDiv.style.display = 'block';
}

// Market Intelligence - Skill Benchmarks
async function loadSkillBenchmarks() {
    const jobTitle = document.getElementById('benchmarkJobTitle').value;
    
    if (!jobTitle) {
        showAlert('benchmarksResult', 'Please enter a job title', 'warning');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/market-intelligence/skill-benchmarks?job_title=${encodeURIComponent(jobTitle)}`);
        const data = await response.json();
        
        if (response.ok) {
            displayBenchmarks(data);
        } else {
            showAlert('benchmarksResult', `Error: ${data.detail || 'Failed to load benchmarks'}`, 'error');
        }
    } catch (error) {
        showAlert('benchmarksResult', `Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayBenchmarks(data) {
    const resultDiv = document.getElementById('benchmarksResult');
    const contentDiv = document.getElementById('benchmarksResultContent');
    
    if (data.message || data.sample_size === 0) {
        contentDiv.innerHTML = `
            <div class="alert alert-warning">
                ${data.message || 'Insufficient data for benchmarks'}
            </div>
            <p>Try analyzing some candidates against this job title first.</p>
        `;
    } else {
        const benchmarks = data.benchmarks || {};
        contentDiv.innerHTML = `
            <div class="result-card">
                <h4>Skill Benchmarks for "${data.job_title}"</h4>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Sample Size</div>
                        <div class="info-value">${data.sample_size}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Mean Score</div>
                        <div class="info-value">${benchmarks.mean?.toFixed(1) || 'N/A'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">P50 (Median)</div>
                        <div class="info-value">${benchmarks.p50 || 'N/A'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">P75</div>
                        <div class="info-value">${benchmarks.p75 || 'N/A'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">P90</div>
                        <div class="info-value">${benchmarks.p90 || 'N/A'}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    resultDiv.style.display = 'block';
}

// Market Insights
async function loadMarketInsights() {
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/market-intelligence/insights`);
        const data = await response.json();
        
        if (response.ok) {
            displayMarketInsights(data);
        } else {
            showAlert('insightsResult', `Error: ${data.detail || 'Failed to load insights'}`, 'error');
        }
    } catch (error) {
        showAlert('insightsResult', `Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayMarketInsights(data) {
    const resultDiv = document.getElementById('insightsResult');
    const contentDiv = document.getElementById('insightsResultContent');
    
    if (data.message) {
        contentDiv.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
    } else {
        contentDiv.innerHTML = `
            <div class="result-card">
                <h4>Market Insights</h4>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Total Candidates</div>
                        <div class="info-value">${data.total_candidates}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Total Analyses</div>
                        <div class="info-value">${data.total_analyses}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Average Match Score</div>
                        <div class="info-value">${data.average_match_score}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Skills Diversity</div>
                        <div class="info-value">${data.skills_diversity} unique skills</div>
                    </div>
                </div>
            </div>
            ${data.top_skills && data.top_skills.length > 0 ? `
            <div class="result-card">
                <h4>Top Skills in Market</h4>
                <ul>
                    ${data.top_skills.map(([skill, count]) => `<li><strong>${skill}</strong> - ${count} occurrence(s)</li>`).join('')}
                </ul>
            </div>
            ` : ''}
        `;
    }
    
    resultDiv.style.display = 'block';
}

// ===== Shortlisting Functions =====

async function loadShortlistCandidates() {
    // Use stored job title from Analyze tab
    if (!currentJobTitle) {
        showAlert('shortlistContainer', 'Please select a job title in the Analyze Candidate tab first', 'warning');
        return;
    }
    
    const jobTitle = currentJobTitle;
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/shortlisting/candidates?job_title=${encodeURIComponent(jobTitle)}`);
        const data = await response.json();
        
        if (response.ok && data.candidates && data.candidates.length > 0) {
            shortlistQueue = data.candidates;
            currentShortlistIndex = 0;
            shortlistedCandidates = [];
            
            // Show container and controls
            document.getElementById('shortlistContainer').style.display = 'block';
            document.getElementById('shortlistControls').style.display = 'flex';
            document.getElementById('shortlistEmpty').style.display = 'none';
            
            // Show first card
            showShortlistCard();
        } else {
            document.getElementById('shortlistContainer').style.display = 'block';
            document.getElementById('shortlistEmpty').style.display = 'block';
            document.getElementById('shortlistControls').style.display = 'none';
            document.getElementById('shortlistCard').style.display = 'none';
            
            const emptyDiv = document.getElementById('shortlistEmpty');
            emptyDiv.innerHTML = '<p>No candidates found. Upload candidates first or try a different job title.</p>';
        }
    } catch (error) {
        showAlert('shortlistContainer', `Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function showShortlistCard() {
    if (currentShortlistIndex >= shortlistQueue.length) {
        document.getElementById('shortlistCard').style.display = 'none';
        document.getElementById('shortlistControls').style.display = 'none';
        document.getElementById('shortlistEmpty').style.display = 'block';
        displayShortlistedSummary();
        return;
    }
    
    const candidate = shortlistQueue[currentShortlistIndex];
    const card = document.getElementById('shortlistCard');
    
    if (!card) return;
    
    const scoreClass = candidate.match_score >= 75 ? 'high' : candidate.match_score >= 50 ? 'medium' : 'low';
    const ideal = candidate.ideal_profile || {};
    const skillAnalysis = candidate.skill_analysis || {};
    
    // Get detailed scoring from analysis (if available from enhanced metadata)
    const sectionScores = candidate.section_scores || {};
    const quickJudgment = candidate.quick_judgment || {};
    const candidateOverview = candidate.candidate_overview || '';
    
    card.innerHTML = `
        <div class="shortlist-card-content">
            <div class="shortlist-card-header">
                <div>
                    <h3>${candidate.name}</h3>
                    ${candidateOverview ? `<p style="color: #666; font-size: 0.95rem; margin-top: 0.25rem;">${candidateOverview}</p>` : ''}
                </div>
                <div class="match-score ${scoreClass}" style="display: inline-block; padding: 0.5rem 1rem; border-radius: 20px; color: white; font-weight: bold; margin-left: 1rem;">
                    ${candidate.match_score}/100
                </div>
            </div>
            
            ${quickJudgment && (quickJudgment.strength_1 || quickJudgment.concern_1) ? `
            <div class="quick-judgment-box">
                <div class="judgment-item positive">
                    <span class="judgment-icon">💪</span>
                    <div>
                        <strong>Strengths:</strong>
                        <div>${quickJudgment.strength_1 || ''}${quickJudgment.strength_2 ? ` • ${quickJudgment.strength_2}` : ''}</div>
                    </div>
                </div>
                <div class="judgment-item negative">
                    <span class="judgment-icon">⚠️</span>
                    <div>
                        <strong>Concerns:</strong>
                        <div>${quickJudgment.concern_1 || ''}${quickJudgment.concern_2 ? ` • ${quickJudgment.concern_2}` : ''}</div>
                    </div>
                </div>
            </div>
            ` : ''}
            
            ${sectionScores && Object.keys(sectionScores).length > 0 ? `
            <div class="section-scores-box">
                <h4 style="margin-bottom: 0.75rem; color: var(--primary-color);">Score Breakdown</h4>
                <div class="scores-grid">
                    <div class="score-item">
                        <span class="score-label">Experience</span>
                        <div class="score-bar">
                            <div class="score-fill" style="width: ${sectionScores.experience || 0}%"></div>
                            <span class="score-value">${sectionScores.experience || 0}</span>
                        </div>
                    </div>
                    <div class="score-item">
                        <span class="score-label">Skills</span>
                        <div class="score-bar">
                            <div class="score-fill" style="width: ${sectionScores.skills || 0}%"></div>
                            <span class="score-value">${sectionScores.skills || 0}</span>
                        </div>
                    </div>
                    <div class="score-item">
                        <span class="score-label">Education</span>
                        <div class="score-bar">
                            <div class="score-fill" style="width: ${sectionScores.education || 0}%"></div>
                            <span class="score-value">${sectionScores.education || 0}</span>
                        </div>
                    </div>
                    <div class="score-item">
                        <span class="score-label">Overall Fit</span>
                        <div class="score-bar">
                            <div class="score-fill" style="width: ${sectionScores.overall_fit || 0}%"></div>
                            <span class="score-value">${sectionScores.overall_fit || 0}</span>
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
            
            <div class="shortlist-details">
                <div class="detail-row">
                    <div class="detail-item">
                        <span class="detail-label">📧 Email:</span>
                        <span class="detail-value">${candidate.email}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">📍 Location:</span>
                        <span class="detail-value">${candidate.location}</span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>💼 Experience</h4>
                    <div class="detail-row">
                        <div class="detail-item">
                            <span class="detail-label">Years of Experience:</span>
                            <span class="detail-value highlight">${candidate.years_experience} years</span>
                            ${ideal.years_experience_required ? `<span style="color: #666; font-size: 0.9rem;"> (Required: ${ideal.years_experience_required} years)</span>` : ''}
                        </div>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>🎓 Education</h4>
                    ${candidate.education && candidate.education.length > 0 ? 
                        candidate.education.map(edu => `
                            <div class="detail-item">
                                <span class="detail-value">${edu.degree} - ${edu.institution}</span>
                                ${edu.field_of_study ? `<span style="color: #666; font-size: 0.9rem;"> (${edu.field_of_study})</span>` : ''}
                            </div>
                        `).join('') : 
                        '<div class="detail-value">No education specified</div>'
                    }
                    ${ideal.education_requirements && ideal.education_requirements.length > 0 ? 
                        `<div style="margin-top: 0.5rem; font-size: 0.85rem; color: #666;">
                            <strong>Required:</strong> ${ideal.education_requirements.join(', ')}
                        </div>` : ''
                    }
                </div>
                
                <div class="detail-section">
                    <h4>✅ Must-Have Skills Match</h4>
                    <div class="skill-match-bar">
                        <div class="skill-match-fill" style="width: ${skillAnalysis.must_have_percentage || 0}%"></div>
                        <span class="skill-match-text">${skillAnalysis.must_have_matches || 0}/${skillAnalysis.must_have_total || 0} (${skillAnalysis.must_have_percentage || 0}%)</span>
                    </div>
                    ${skillAnalysis.skill_gaps && skillAnalysis.skill_gaps.length > 0 ? `
                        <div style="margin-top: 0.5rem; color: #e74c3c; font-size: 0.9rem;">
                            <strong>Missing:</strong> ${skillAnalysis.skill_gaps.slice(0, 5).join(', ')}${skillAnalysis.skill_gaps.length > 5 ? '...' : ''}
                        </div>
                    ` : ''}
                </div>
                
                <div class="detail-section">
                    <h4>🛠️ Key Skills</h4>
                    <div class="skills-tags">
                        ${(candidate.skills || []).slice(0, 10).map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
                        ${candidate.skills && candidate.skills.length > 10 ? `<span class="skill-tag">+${candidate.skills.length - 10} more</span>` : ''}
                    </div>
                </div>
                
                ${candidate.key_matches && candidate.key_matches.length > 0 ? `
                <div class="detail-section">
                    <h4>✓ Key Matches</h4>
                    <ul class="matches-list">
                        ${candidate.key_matches.slice(0, 5).map(match => `<li>${match}</li>`).join('')}
                    </ul>
                </div>
                ` : ''}
                
                ${candidate.gaps && candidate.gaps.length > 0 ? `
                <div class="detail-section">
                    <h4>⚠️ Skill Gaps</h4>
                    <ul class="gaps-list">
                        ${candidate.gaps.slice(0, 5).map(gap => `<li>${gap}</li>`).join('')}
                    </ul>
                </div>
                ` : ''}
            </div>
        </div>
    `;
    
    card.style.display = 'block';
}

function shortlistCandidate() {
    if (currentShortlistIndex >= shortlistQueue.length) return;
    
    const candidate = shortlistQueue[currentShortlistIndex];
    shortlistedCandidates.push(candidate);
    
    currentShortlistIndex++;
    showShortlistCard();
}

function rejectCandidate() {
    currentShortlistIndex++;
    showShortlistCard();
}

function displayShortlistedSummary() {
    const summaryDiv = document.getElementById('shortlistedSummary');
    const contentDiv = document.getElementById('shortlistedContent');
    
    if (!summaryDiv || !contentDiv) return;
    
    if (shortlistedCandidates.length === 0) {
        summaryDiv.style.display = 'none';
        return;
    }
    
    contentDiv.innerHTML = `
        <div class="result-card">
            <h4>⭐ ${shortlistedCandidates.length} Candidate(s) Shortlisted</h4>
            <div class="shortlisted-grid">
                ${shortlistedCandidates.map(c => `
                    <div class="shortlisted-item">
                        <h5>${c.name}</h5>
                        <p><strong>Match Score:</strong> ${c.match_score}/100</p>
                        <p><strong>Experience:</strong> ${c.years_experience} years</p>
                        <p><strong>Email:</strong> ${c.email}</p>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    summaryDiv.style.display = 'block';
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
