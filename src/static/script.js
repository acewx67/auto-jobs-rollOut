document.addEventListener('DOMContentLoaded', () => {
    const resumeUpload = document.getElementById('resume-upload');
    const resumeText = document.getElementById('resume-text');
    const jobDescription = document.getElementById('job-description');
    const tailorBtn = document.getElementById('tailor-btn');
    const dropZone = document.getElementById('drop-zone');
    const fileNameDisplay = document.getElementById('file-name');
    const resultsSection = document.getElementById('results');
    const loader = tailorBtn.querySelector('.loader');
    const btnText = tailorBtn.querySelector('.btn-text');

    // Drag and drop logic
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('active'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('active'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            resumeUpload.files = files;
            updateFileName(files[0].name);
        }
    });

    dropZone.addEventListener('click', () => resumeUpload.click());

    resumeUpload.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            updateFileName(e.target.files[0].name);
        }
    });

    function updateFileName(name) {
        fileNameDisplay.textContent = name;
        fileNameDisplay.style.color = 'var(--accent-color)';
    }

    // Main tailoring logic
    tailorBtn.addEventListener('click', async () => {
        const resumeFile = resumeUpload.files[0];
        const resumeRawText = resumeText.value.trim();
        const jobDescText = jobDescription.value.trim();

        if (!resumeFile && !resumeRawText) {
            alert('Please upload a resume file or paste your resume text.');
            return;
        }

        if (!jobDescText) {
            alert('Please paste a job description.');
            return;
        }

        // Set loading state
        tailorBtn.disabled = true;
        loader.hidden = false;
        btnText.textContent = 'Tailoring...';
        resultsSection.hidden = true;

        try {
            const formData = new FormData();
            formData.append('job_description', jobDescText);
            formData.append('output_format', 'latex-pdf');

            if (resumeFile) {
                formData.append('resume', resumeFile);
            } else {
                // If only text is provided, we need to create a temporary blob/file
                const blob = new Blob([resumeRawText], { type: 'text/plain' });
                formData.append('resume', blob, 'resume.txt');
            }

            const response = await fetch('/api/tailor', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Tailoring failed');
            }

            const data = await response.json();
            displayResults(data);

        } catch (error) {
            console.error('Error:', error);
            alert(`Error: ${error.message}`);
        } finally {
            tailorBtn.disabled = false;
            loader.hidden = true;
            btnText.textContent = 'Tailor My Resume';
        }
    });

    function displayResults(data) {
        // Update scores
        document.getElementById('original-score').textContent = Math.round(data.original_ats_score);
        document.getElementById('final-score').textContent = Math.round(data.final_ats_score);
        
        const improvement = data.ats_improvement_percentage;
        const badge = document.getElementById('improvement-badge');
        badge.textContent = `+${improvement}% Improvement`;
        
        // Update key changes
        const changesList = document.getElementById('key-changes');
        changesList.innerHTML = '';
        if (data.key_changes && data.key_changes.length > 0) {
            data.key_changes.forEach(change => {
                const li = document.createElement('li');
                li.textContent = change;
                changesList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'Optimized keywords and structured for ATS readability.';
            changesList.appendChild(li);
        }

        // Update download link
        const downloadLink = document.getElementById('download-link');
        downloadLink.href = data.download_url;
        // Extract filename from download_url
        const filename = data.download_url.split('/').pop();
        downloadLink.setAttribute('download', filename);
        
        // Show results
        resultsSection.hidden = false;
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
});
