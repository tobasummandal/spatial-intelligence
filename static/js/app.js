// Global state
let currentFolders = [];
let eventSource = null;
let selectedFile = null;
let currentTempDir = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadTemplates();
    setupTemplateToggle();
    setupFileUpload();
});

// Load available templates
async function loadTemplates() {
    try {
        const response = await fetch('/api/templates');
        const templates = await response.json();
        
        const select = document.getElementById('template_file');
        select.innerHTML = '';
        
        if (templates.length === 0) {
            select.innerHTML = '<option value="">No templates found</option>';
        } else {
            templates.forEach(template => {
                const option = document.createElement('option');
                option.value = template;
                option.textContent = template;
                if (template === 'example_template.json') {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading templates:', error);
    }
}

// Setup template type toggle
function setupTemplateToggle() {
    const radios = document.querySelectorAll('input[name="template_type"]');
    radios.forEach(radio => {
        radio.addEventListener('change', function() {
            const fileSection = document.getElementById('template-file-section');
            const inlineSection = document.getElementById('template-inline-section');
            
            if (this.value === 'file') {
                fileSection.style.display = 'flex';
                inlineSection.style.display = 'none';
            } else {
                fileSection.style.display = 'none';
                inlineSection.style.display = 'block';
            }
        });
    });
}

// Setup file upload (drag & drop and click)
function setupFileUpload() {
    const dropZone = document.getElementById('file-drop-zone');
    const fileInput = document.getElementById('file-input');
    
    // Click to select file
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File selected via input
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
    
    // Drag and drop handlers
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });
}

// Handle file selection
function handleFile(file) {
    const allowedExtensions = ['.obj', '.glb', '.gltf', '.fbx', '.stl', '.ply', '.dae', '.blend', '.3ds', '.x3d'];
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!allowedExtensions.includes(ext)) {
        alert(`File type not supported. Please use one of: ${allowedExtensions.join(', ')}`);
        return;
    }
    
    selectedFile = file;
    
    // Show file info
    document.getElementById('file-drop-zone').style.display = 'none';
    document.getElementById('file-info').style.display = 'block';
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-size').textContent = formatFileSize(file.size);
}

// Clear selected file
function clearFile() {
    selectedFile = null;
    document.getElementById('file-drop-zone').style.display = 'block';
    document.getElementById('file-info').style.display = 'none';
    document.getElementById('file-input').value = '';
}

// Format file size
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// Load template preview
async function loadTemplatePreview() {
    const templateType = document.querySelector('input[name="template_type"]:checked').value;
    const previewDiv = document.getElementById('template-preview');
    const previewContent = document.getElementById('template-preview-content');
    
    try {
        let template;
        
        if (templateType === 'file') {
            const filename = document.getElementById('template_file').value;
            if (!filename) {
                alert('Please select a template file');
                return;
            }
            const response = await fetch(`/api/template/${filename}`);
            template = await response.json();
        } else {
            const inlineText = document.getElementById('inline_template').value;
            if (!inlineText) {
                alert('Please enter template JSON');
                return;
            }
            template = JSON.parse(inlineText);
        }
        
        previewContent.textContent = JSON.stringify(template, null, 2);
        previewDiv.style.display = 'block';
    } catch (error) {
        alert('Error loading template: ' + error.message);
    }
}

// Load folders
async function loadFolders() {
    const parentDir = document.getElementById('parent_dir').value;
    const foldersList = document.getElementById('folders-list');
    
    foldersList.innerHTML = '<p class="placeholder">Loading folders...</p>';
    
    try {
        const response = await fetch('/api/folders', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({parent_dir: parentDir})
        });
        
        const data = await response.json();
        
        if (data.error) {
            foldersList.innerHTML = `<p class="placeholder error">${data.error}</p>`;
            return;
        }
        
        currentFolders = data;
        
        if (data.length === 0) {
            foldersList.innerHTML = '<p class="placeholder">No folders found</p>';
            return;
        }
        
        foldersList.innerHTML = '';
        data.forEach(folder => {
            const folderDiv = document.createElement('div');
            folderDiv.className = 'folder-item' + (folder.has_output ? ' has-output' : '');
            folderDiv.innerHTML = `
                <h4>${folder.uid}</h4>
                <p>${folder.num_images} images</p>
                <p>${folder.has_output ? '✓ Output available' : '⏳ Not processed'}</p>
            `;
            
            if (folder.has_output) {
                folderDiv.addEventListener('click', () => viewResults(folder));
            }
            
            foldersList.appendChild(folderDiv);
        });
    } catch (error) {
        foldersList.innerHTML = `<p class="placeholder error">Error: ${error.message}</p>`;
    }
}

// View results for a folder
async function viewResults(folder) {
    switchTab('viewer');
    
    const resultsViewer = document.getElementById('results-viewer');
    const imagesGrid = document.getElementById('images-grid');
    const jsonOutput = document.getElementById('json-output');
    
    resultsViewer.style.display = 'block';
    imagesGrid.innerHTML = '<p class="placeholder">Loading images...</p>';
    jsonOutput.textContent = 'Loading output...';
    
    try {
        // Load images
        const imagesResponse = await fetch(`/api/images/${encodeURIComponent(folder.path)}`);
        const images = await imagesResponse.json();
        
        imagesGrid.innerHTML = '';
        images.forEach(img => {
            const imgDiv = document.createElement('div');
            imgDiv.className = 'image-item';
            imgDiv.innerHTML = `
                <img src="${img.data}" alt="${img.name}">
                <p>${img.name}</p>
            `;
            imagesGrid.appendChild(imgDiv);
        });
        
        // Load output JSON
        const outputResponse = await fetch(`/api/output/${encodeURIComponent(folder.path)}`);
        const output = await outputResponse.json();
        
        jsonOutput.textContent = JSON.stringify(output, null, 2);
    } catch (error) {
        imagesGrid.innerHTML = `<p class="placeholder error">Error loading images: ${error.message}</p>`;
        jsonOutput.textContent = `Error loading output: ${error.message}`;
    }
}

// Switch tabs
function switchTab(tabName) {
    // Update tab buttons
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
        if (tab.textContent.toLowerCase().includes(tabName)) {
            tab.classList.add('active');
        }
    });
    
    // Update tab content
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => content.classList.remove('active'));
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// Start processing (either upload or existing)
async function startProcessing() {
    const workflowType = document.querySelector('input[name="workflow_type"]:checked').value;
    
    if (workflowType === 'upload') {
        await uploadAndProcess();
    } else {
        await runScript();
    }
}

// Upload and process 3D file
async function uploadAndProcess() {
    if (!selectedFile) {
        alert('Please select a 3D file to upload');
        return;
    }
    
    const apiKey = document.getElementById('api_key').value;
    if (!apiKey) {
        alert('Please enter your Claude API key');
        return;
    }
    
    // Gather configuration
    const config = {
        api_key: apiKey,
        model: document.getElementById('model').value,
        num_views: parseInt(document.getElementById('num_views').value),
        max_tokens: parseInt(document.getElementById('max_tokens').value),
        rate_limit_delay: parseFloat(document.getElementById('rate_limit_delay').value),
        use_diffurank: document.getElementById('use_diffurank').checked
    };
    
    // Handle template
    const templateType = document.querySelector('input[name="template_type"]:checked').value;
    if (templateType === 'file') {
        config.template_file = document.getElementById('template_file').value;
        config.use_inline_template = false;
    } else {
        const inlineText = document.getElementById('inline_template').value;
        if (!inlineText) {
            alert('Please enter template JSON');
            return;
        }
        try {
            config.inline_template = JSON.parse(inlineText);
            config.use_inline_template = true;
        } catch (error) {
            alert('Invalid JSON in inline template: ' + error.message);
            return;
        }
    }
    
    // Switch to progress tab
    switchTab('progress');
    
    // Update UI
    document.getElementById('run-btn').style.display = 'none';
    document.getElementById('stop-btn').style.display = 'block';
    
    // Clear progress output
    const progressOutput = document.getElementById('progress-output');
    progressOutput.innerHTML = '<p class="progress-line">📤 Uploading file and starting processing...</p>';
    
    // Create FormData
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('config', JSON.stringify(config));
    
    try {
        // Upload and start processing
        const response = await fetch('/api/upload-and-process', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.status === 'started') {
            currentTempDir = result.temp_dir;
            progressOutput.innerHTML += '<p class="progress-line success">✓ File uploaded successfully!</p>';
            progressOutput.innerHTML += '<p class="progress-line">Starting workflow...</p>';
            
            // Connect to progress stream
            connectUploadProgressStream();
        } else {
            progressOutput.innerHTML += `<p class="progress-line error">Error: ${result.error || 'Unknown error'}</p>`;
            resetRunButton();
        }
    } catch (error) {
        progressOutput.innerHTML += `<p class="progress-line error">Error: ${error.message}</p>`;
        resetRunButton();
    }
}

// Connect to progress stream for upload workflow
function connectUploadProgressStream() {
    if (eventSource) {
        eventSource.close();
    }
    
    eventSource = new EventSource('/api/progress');
    const progressOutput = document.getElementById('progress-output');
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'output') {
            const line = document.createElement('p');
            line.className = 'progress-line';
            
            // Color code based on content
            if (data.data.includes('✓') || data.data.includes('Success')) {
                line.className += ' success';
            } else if (data.data.includes('✗') || data.data.includes('Error') || data.data.includes('Failed')) {
                line.className += ' error';
            }
            
            line.textContent = data.data;
            progressOutput.appendChild(line);
            progressOutput.scrollTop = progressOutput.scrollHeight;
        } else if (data.type === 'complete' && data.data) {
            // Display results
            const line = document.createElement('p');
            line.className = 'progress-line success';
            line.textContent = '\n✓ Processing complete! Displaying results...';
            progressOutput.appendChild(line);
            
            eventSource.close();
            eventSource = null;
            resetRunButton();
            
            // Display results
            displayUploadResults(data.data);
            
            // Clean up temp directory
            if (currentTempDir) {
                cleanupTemp(currentTempDir);
            }
        } else if (data.type === 'error') {
            const line = document.createElement('p');
            line.className = 'progress-line error';
            line.textContent = `\n✗ Error: ${data.data}`;
            progressOutput.appendChild(line);
            
            eventSource.close();
            eventSource = null;
            resetRunButton();
            
            // Clean up temp directory
            if (currentTempDir) {
                cleanupTemp(currentTempDir);
            }
        }
    };
    
    eventSource.onerror = function(error) {
        console.error('EventSource error:', error);
        eventSource.close();
        eventSource = null;
        resetRunButton();
    };
}

// Display upload results
function displayUploadResults(data) {
    switchTab('viewer');
    
    const resultsViewer = document.getElementById('results-viewer');
    const imagesGrid = document.getElementById('images-grid');
    const jsonOutput = document.getElementById('json-output');
    
    resultsViewer.style.display = 'block';
    
    // Display images
    imagesGrid.innerHTML = '';
    data.images.forEach(img => {
        const imgDiv = document.createElement('div');
        imgDiv.className = 'image-item';
        imgDiv.innerHTML = `
            <img src="${img.data}" alt="${img.name}">
            <p>${img.name}</p>
        `;
        imagesGrid.appendChild(imgDiv);
    });
    
    // Display JSON
    jsonOutput.textContent = JSON.stringify(data.json_output, null, 2);
}

// Clean up temporary directory
async function cleanupTemp(tempDir) {
    try {
        await fetch('/api/cleanup', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({temp_dir: tempDir})
        });
    } catch (error) {
        console.error('Cleanup error:', error);
    }
}

// Run script (existing workflow)
async function runScript() {
    const apiKey = document.getElementById('api_key').value;
    if (!apiKey) {
        alert('Please enter your Claude API key');
        return;
    }
    
    // Gather all configuration
    const config = {
        api_key: apiKey,
        parent_dir: document.getElementById('parent_dir').value,
        model: document.getElementById('model').value,
        num_views: parseInt(document.getElementById('num_views').value),
        max_tokens: parseInt(document.getElementById('max_tokens').value),
        rate_limit_delay: parseFloat(document.getElementById('rate_limit_delay').value),
        use_diffurank: document.getElementById('use_diffurank').checked,
        overwrite: document.getElementById('overwrite').checked
    };
    
    // Handle template
    const templateType = document.querySelector('input[name="template_type"]:checked').value;
    if (templateType === 'file') {
        config.template_file = document.getElementById('template_file').value;
        config.use_inline_template = false;
    } else {
        const inlineText = document.getElementById('inline_template').value;
        if (!inlineText) {
            alert('Please enter template JSON');
            return;
        }
        try {
            config.inline_template = JSON.parse(inlineText);
            config.use_inline_template = true;
        } catch (error) {
            alert('Invalid JSON in inline template: ' + error.message);
            return;
        }
    }
    
    // Switch to progress tab
    switchTab('progress');
    
    // Update UI
    document.getElementById('run-btn').style.display = 'none';
    document.getElementById('stop-btn').style.display = 'block';
    
    // Clear progress output
    const progressOutput = document.getElementById('progress-output');
    progressOutput.innerHTML = '<p class="progress-line">Starting script...</p>';
    
    try {
        // Start script
        const response = await fetch('/api/run', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (result.status === 'started') {
            // Connect to progress stream
            connectProgressStream();
        } else {
            progressOutput.innerHTML += `<p class="progress-line error">Error: ${result.error || 'Unknown error'}</p>`;
            resetRunButton();
        }
    } catch (error) {
        progressOutput.innerHTML += `<p class="progress-line error">Error: ${error.message}</p>`;
        resetRunButton();
    }
}

// Connect to progress stream
function connectProgressStream() {
    if (eventSource) {
        eventSource.close();
    }
    
    eventSource = new EventSource('/api/progress');
    const progressOutput = document.getElementById('progress-output');
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'output') {
            const line = document.createElement('p');
            line.className = 'progress-line';
            
            // Color code based on content
            if (data.data.includes('✓') || data.data.includes('Success')) {
                line.className += ' success';
            } else if (data.data.includes('✗') || data.data.includes('Error') || data.data.includes('Failed')) {
                line.className += ' error';
            }
            
            line.textContent = data.data;
            progressOutput.appendChild(line);
            progressOutput.scrollTop = progressOutput.scrollHeight;
        } else if (data.type === 'complete') {
            const line = document.createElement('p');
            line.className = 'progress-line success';
            line.textContent = '\n✓ Script completed!';
            progressOutput.appendChild(line);
            
            eventSource.close();
            eventSource = null;
            resetRunButton();
            
            // Refresh folders
            loadFolders();
        } else if (data.type === 'error') {
            const line = document.createElement('p');
            line.className = 'progress-line error';
            line.textContent = `\n✗ Error: ${data.data}`;
            progressOutput.appendChild(line);
            
            eventSource.close();
            eventSource = null;
            resetRunButton();
        }
    };
    
    eventSource.onerror = function(error) {
        console.error('EventSource error:', error);
        eventSource.close();
        eventSource = null;
        resetRunButton();
    };
}

// Stop script
async function stopScript() {
    try {
        await fetch('/api/stop', {method: 'POST'});
        
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
        
        const progressOutput = document.getElementById('progress-output');
        const line = document.createElement('p');
        line.className = 'progress-line error';
        line.textContent = '\n⬛ Script stopped by user';
        progressOutput.appendChild(line);
        
        resetRunButton();
    } catch (error) {
        alert('Error stopping script: ' + error.message);
    }
}

// Reset run button
function resetRunButton() {
    document.getElementById('run-btn').style.display = 'block';
    document.getElementById('stop-btn').style.display = 'none';
}

