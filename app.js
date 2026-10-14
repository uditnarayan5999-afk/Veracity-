document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('textInput');
    const wordCount = document.getElementById('wordCount');
    const analyzerForm = document.getElementById('analyzerForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const btnText = document.querySelector('.btn-text');
    const btnSpinner = document.getElementById('btnSpinner');
    const resultsSection = document.getElementById('resultsSection');
    
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const fileOverlay = document.getElementById('fileOverlay');
    const overlayFilename = document.getElementById('overlayFilename');
    const removeFileBtn = document.getElementById('removeFileBtn');

    let currentFile = null;

    // Word Count Tracker
    textInput.addEventListener('input', () => {
        const text = textInput.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        wordCount.textContent = `${words} word${words !== 1 ? 's' : ''}`;
    });

    // Drag and Drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () =>
        dropZone.classList.add('drag-active'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-active'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt.files && dt.files.length > 0) {
            handleFileSelection(dt.files[0]);
        }
    });

    // File Input button functionality
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    function handleFileSelection(file) {
        currentFile = file;
        overlayFilename.textContent = file.name;
        fileOverlay.classList.remove('hidden');
        textInput.classList.add('hidden');
        wordCount.textContent = `FILE MOUNTED`;
    }

    removeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        currentFile = null;
        fileInput.value = '';
        fileOverlay.classList.add('hidden');
        textInput.classList.remove('hidden');
        
        // Restore word count
        const text = textInput.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        wordCount.textContent = `${words} word${words !== 1 ? 's' : ''}`;
    });

    analyzerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!currentFile && (!textInput.value.trim() || textInput.value.trim().split(/\s+/).length < 3)) {
            alert('Please provide text or upload a file for analysis.');
            return;
        }

        setLoadingState(true);

        try {
            let response;
            
            // Dispatch Multipart form data if file uploaded, else standard payload
            if (currentFile) {
                const formData = new FormData();
                formData.append('file', currentFile);
                
                response = await fetch('http://localhost:8000/api/check_file', {
                    method: 'POST',
                    body: formData
                });
            } else {
                response = await fetch('http://localhost:8000/api/check', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: textInput.value.trim() })
                });
            }

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Analysis connection failed.');
            }

            const data = await response.json();
            renderResults(data);
            
        } catch (error) {
            console.error(error);
            alert(`Analysis Error: ${error.message}\nPlease verify your backend is active.`);
        } finally {
            setLoadingState(false);
        }
    });

    function setLoadingState(isLoading) {
        if (isLoading) {
            analyzeBtn.disabled = true;
            btnText.textContent = currentFile ? 'Extracting text...' : 'Analyzing...';
            btnSpinner.classList.remove('hidden');
            resultsSection.classList.add('hidden');
        } else {
            analyzeBtn.disabled = false;
            btnText.textContent = 'Analyze Content';
            btnSpinner.classList.add('hidden');
        }
    }

    function renderResults(data) {
        const percentage = Math.round(data.overall_score * 100);
        const scoreColor = percentage > 30 ? 'var(--danger)' : 'var(--success)';
        
        let detailsHtml = '';
        data.details.forEach((item) => {
            const isPlag = item.is_plagiarized;
            const cardClass = isPlag ? 'sentence-plagiarized' : 'sentence-original';
            const textClass = isPlag ? 's-plagiarized-text' : '';
            
            let sourceHtml = '';
            if (isPlag && item.matched_url) {
                sourceHtml = `<div class="s-source">Source: <a href="${item.matched_url}" target="_blank">View reference</a></div>`;
            } else if (isPlag) {
                sourceHtml = `<div class="s-source" style="color:var(--danger)">Hidden source detected</div>`;
            }

            detailsHtml += `
                <div class="sentence-card ${cardClass}">
                    <div class="s-text ${textClass}">${item.sentence}</div>
                    <div class="s-meta">
                        <div>Similarity Index: ${Math.round(item.similarity_score * 100)}%</div>
                        ${sourceHtml}
                    </div>
                </div>
            `;
        });
        
        const aiProb = data.ai_probability || 0;
        const aiColor = aiProb > 65 ? 'var(--danger)' : (aiProb > 30 ? '#f59e0b' : 'var(--success)');
        const aiStats = `
            <div class="ai-block">
                <h3>Synthetic Authenticity Report</h3>
                <div class="ai-flex">
                    <span style="color: var(--text-muted)">Project Classification: <span style="color: var(--text-white); font-weight: 600;">${data.is_code_detected ? 'Source Code' : 'Natural Language'}</span></span>
                    <span style="color: ${aiColor}; font-weight: 700;">Synthetic Score: ${aiProb}%</span>
                </div>
                <div class="ai-bar-bg">
                    <div class="ai-bar-fill" style="width: ${aiProb}%; background: ${aiColor}; color: ${aiColor}"></div>
                </div>
            </div>
        `;

        resultsSection.innerHTML = `
            <div class="result-block">
                <div class="score-display">
                    <span class="score-number" style="color: ${scoreColor}">${percentage}%</span>
                    <span class="score-label">Plagiarized Percentage</span>
                </div>
                <p style="color: var(--text-muted); font-size: 1.1rem; margin-bottom: 2rem;">
                    Our scan identified ${data.plagiarized_sentences_count} matching segments out of ${data.total_analyzed_sentences} analyzed blocks.
                </p>
            </div>

            ${aiStats}

            <div class="results-breakdown">
                <h3 class="result-h3">Content Breakdown</h3>
                ${detailsHtml}
            </div>

            <div style="margin-top: 3rem; display: flex; justify-content: center;">
                <button class="btn-hero" style="font-size: 1rem; padding: 0.8rem 2rem;" onclick="document.getElementById('resultsSection').classList.add('hidden'); window.scrollTo({top: 0, behavior: 'smooth'});">New Analysis</button>
            </div>
        `;
        
        resultsSection.classList.remove('hidden');
        setTimeout(() => { resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 100);
    }
});

