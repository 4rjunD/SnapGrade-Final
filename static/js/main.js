// Rubiq - AI Grading Platform JavaScript

// Rubric data by assignment type
const rubrics = {
    "Essay": [
        { id: "essay-basic", name: "Basic Essay Rubric", content: "Content (40%): Addresses the prompt fully and develops ideas thoroughly.\nOrganization (30%): Clear structure with introduction, body paragraphs, and conclusion.\nLanguage (20%): Uses varied sentence structure and sophisticated vocabulary.\nMechanics (10%): Proper grammar, spelling, and punctuation." },
        { id: "essay-advanced", name: "Advanced Essay Rubric", content: "Thesis (25%): Clear, specific thesis that addresses the prompt and provides direction.\nEvidence (25%): Relevant, specific evidence that supports the thesis.\nAnalysis (25%): Thoughtful analysis that connects evidence to thesis.\nOrganization (15%): Logical structure with clear transitions.\nStyle (10%): Sophisticated vocabulary, varied sentence structure, and appropriate tone." }
    ],
    "Short Answer": [
        { id: "short-basic", name: "Basic Short Answer Rubric", content: "Accuracy (50%): Answer is factually correct and addresses the question.\nCompleteness (30%): Answer includes all necessary components.\nClarity (20%): Answer is clearly written and easy to understand." },
        { id: "short-detailed", name: "Detailed Short Answer Rubric", content: "Accuracy (40%): Answer is factually correct and addresses the question.\nCompleteness (30%): Answer includes all necessary components.\nEvidence (20%): Answer includes specific evidence or examples.\nClarity (10%): Answer is clearly written and easy to understand." }
    ],
    "Problem Set": [
        { id: "problem-math", name: "Math Problem Set Rubric", content: "Correct Answer (40%): Final answer is correct.\nWork Shown (40%): All steps are shown clearly.\nMathematical Notation (10%): Proper mathematical notation is used.\nOrganization (10%): Work is organized and easy to follow." },
        { id: "problem-science", name: "Science Problem Set Rubric", content: "Correct Answer (30%): Final answer is correct.\nMethodology (30%): Appropriate scientific method or approach is used.\nWork Shown (30%): All steps are shown clearly.\nPresentation (10%): Work is organized and uses proper scientific notation." }
    ],
    "Multiple Choice": [
        { id: "mc-basic", name: "Basic Multiple Choice Rubric", content: "Correct Answer (100%): Each question is worth equal points based on selecting the correct option." },
        { id: "mc-weighted", name: "Weighted Multiple Choice Rubric", content: "Correct Answer (varies): Questions are weighted based on difficulty. Easy (5 points), Medium (10 points), Hard (15 points)." }
    ],
    "Code": [
        { id: "code-basic", name: "Basic Code Rubric", content: "Functionality (50%): Code works as expected and meets requirements.\nEfficiency (20%): Code uses efficient algorithms and data structures.\nReadability (20%): Code is well-organized and includes appropriate comments.\nStyle (10%): Code follows language-specific style guidelines." },
        { id: "code-advanced", name: "Advanced Code Rubric", content: "Functionality (40%): Code works as expected and meets all requirements.\nEfficiency (20%): Code uses efficient algorithms and data structures.\nReadability (15%): Code is well-organized and includes appropriate comments.\nError Handling (15%): Code handles potential errors appropriately.\nTesting (10%): Code includes comprehensive tests." }
    ]
};

// Global variable to store loaded rubrics
let loadedRubrics = [];

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const assignmentTypeSelect = document.getElementById('assignment-type');
    const rubricSelect = document.getElementById('rubric-select');
    const rubricPreview = document.getElementById('rubric-preview');
    const rubricToggle = document.getElementById('rubric-toggle');
    const gradingForm = document.getElementById('grading-form');
    const submissionTextarea = document.getElementById('submission');
    const fileUpload = document.getElementById('file-upload');
    const loadingIndicator = document.querySelector('.loading');
    const resultCard = document.getElementById('results-section');
    const scoreDisplay = document.getElementById('score-display');
    const feedbackDisplay = document.getElementById('feedback-display');
    const extractedTextSection = document.getElementById('extracted-text-section');
    const extractedText = document.getElementById('extracted-text');
    const customRubricTextarea = document.getElementById('custom-rubric');
    const customRubricSection = document.getElementById('custom-rubric-section');
    const rubricUploadSection = document.getElementById('rubric-upload-section');
    const rubricUpload = document.getElementById('rubric-upload');
    const rubricFilePreview = document.getElementById('rubric-file-preview');
    const rubricFileName = document.getElementById('rubric-file-name');
    
    // Initialize drag-and-drop zones
    initializeSingleFileDropZone();
    initializeRubricDropZone();
    
    // Batch upload elements
    const batchUpload = document.getElementById('batch-upload');
    const batchFileList = document.getElementById('batch-file-list');
    const batchResultsSection = document.getElementById('batch-results-section');
    const batchSummary = document.getElementById('batch-summary');
    const batchResultsContent = document.getElementById('batch-results-content');
    
    // Variable to store uploaded rubric content
    let uploadedRubricContent = null;
    
    // Add click debugging for file upload
    const fileUploadLabel = document.querySelector('label[for="file-upload"]');
    if (fileUploadLabel) {
        fileUploadLabel.addEventListener('click', function(e) {
            console.log('Upload label clicked');
        });
    }
    
    // Add debugging for file input click
    if (fileUpload) {
        fileUpload.addEventListener('click', function(e) {
            console.log('File input clicked');
        });
    }
    
    // Toggle required attribute on submission textarea based on file upload
    if (fileUpload && submissionTextarea) {
        fileUpload.addEventListener('change', function() {
            console.log('File upload change event triggered:', this.files.length);
            if (this.files.length > 0) {
                console.log('File selected:', this.files[0].name);
                // If file is uploaded, submission text is not required
                submissionTextarea.removeAttribute('required');
                
                // Show file name in upload area
                const uploadText = document.querySelector('#file-content .upload-text');
                if (uploadText) {
                    uploadText.textContent = `Selected: ${this.files[0].name}`;
                }
            } else {
                console.log('No file selected');
                // If no file is uploaded, submission text is required
                submissionTextarea.setAttribute('required', 'required');
                
                // Reset upload text
                const uploadText = document.querySelector('#file-content .upload-text');
                if (uploadText) {
                    uploadText.textContent = 'Click to upload assignment';
                }
            }
        });
    }
    
    // Handle batch file upload
    if (batchUpload && batchFileList) {
        batchUpload.addEventListener('change', function() {
            const files = Array.from(this.files);
            
            if (files.length > 0) {
                // Update upload text
                const uploadText = document.querySelector('#batch-content .upload-text');
                if (uploadText) {
                    uploadText.textContent = `${files.length} file(s) selected`;
                }
                
                // Display file list
                batchFileList.innerHTML = '';
                files.forEach((file, index) => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'batch-file-item';
                    fileItem.innerHTML = `
                        <i class="fas fa-file"></i>
                        <span class="file-name">${file.name}</span>
                        <span class="file-size">(${formatFileSize(file.size)})</span>
                        <button type="button" class="remove-file" data-index="${index}">
                            <i class="fas fa-times"></i>
                        </button>
                    `;
                    batchFileList.appendChild(fileItem);
                });
                
                // Add remove file functionality
                batchFileList.querySelectorAll('.remove-file').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const index = parseInt(this.dataset.index);
                        removeFileFromBatch(index);
                    });
                });
                
                // Make submission text not required when files are selected
                if (submissionTextarea) {
                    submissionTextarea.removeAttribute('required');
                }
            } else {
                // Reset if no files
                const uploadText = document.querySelector('#batch-content .upload-text');
                if (uploadText) {
                    uploadText.textContent = 'Click to upload multiple assignments';
                }
                batchFileList.innerHTML = '';
                
                if (submissionTextarea) {
                    submissionTextarea.setAttribute('required', 'required');
                }
            }
        });
    }

    // Populate rubric dropdown based on assignment type selection
    assignmentTypeSelect.addEventListener('change', function() {
        const assignmentType = this.value;
        
        // Clear existing options
        rubricSelect.innerHTML = '<option value="" selected disabled>Select Rubric</option>';
        rubricSelect.innerHTML += '<option value="custom">Custom Rubric (Text)</option>';
        rubricSelect.innerHTML += '<option value="upload">Upload Rubric File</option>';
        
        // Add built-in rubrics for the selected assignment type
        if (selectedType && rubrics[selectedType]) {
            rubrics[selectedType].forEach(rubric => {
                const option = document.createElement('option');
                option.value = rubric.id;
                option.textContent = rubric.name;
                option.dataset.content = rubric.content;
                rubricSelect.appendChild(option);
            });
        }
        
        // Add custom rubrics from database that match the assignment type
        if (loadedRubrics && loadedRubrics.length > 0) {
            const matchingRubrics = loadedRubrics.filter(rubric => 
                rubric.type === selectedType || selectedType === 'Other'
            );
            
            if (matchingRubrics.length > 0) {
                // Add separator
                const separator = document.createElement('option');
                separator.disabled = true;
                separator.textContent = '--- Custom Rubrics ---';
                rubricSelect.appendChild(separator);
                
                // Add custom rubrics
                matchingRubrics.forEach(rubric => {
                    const option = document.createElement('option');
                    option.value = 'custom-' + rubric.id;
                    option.textContent = rubric.name + ' (Custom)';
                    option.dataset.content = rubric.content;
                    rubricSelect.appendChild(option);
                });
            }
        }

        // Hide custom rubric section when changing assignment type
        if (customRubricSection) {
            customRubricSection.style.display = 'none';
        }
        
        // Hide rubric upload section when changing assignment type
        if (rubricUploadSection) {
            rubricUploadSection.style.display = 'none';
        }

        // Hide rubric preview
        if (rubricPreview) {
            rubricPreview.style.display = 'none';
        }
        
        // Reset uploaded rubric content
        uploadedRubricContent = null;
    });

    // Handle rubric selection
    if (rubricSelect) {
        rubricSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            
            // Show/hide appropriate rubric input sections
            if (customRubricSection && rubricUploadSection) {
                if (this.value === 'custom') {
                    customRubricSection.style.display = 'block';
                    rubricUploadSection.style.display = 'none';
                    if (rubricPreview) {
                        rubricPreview.textContent = '';
                        rubricPreview.style.display = 'none';
                    }
                    uploadedRubricContent = null;
                } else if (this.value === 'upload') {
                    customRubricSection.style.display = 'none';
                    rubricUploadSection.style.display = 'block';
                    if (rubricPreview) {
                        rubricPreview.textContent = '';
                        rubricPreview.style.display = 'none';
                    }
                } else {
                    customRubricSection.style.display = 'none';
                    rubricUploadSection.style.display = 'none';
                    if (rubricPreview && selectedOption.dataset.content) {
                        rubricPreview.textContent = selectedOption.dataset.content;
                    }
                    uploadedRubricContent = null;
                }
            }
        });
    }

    // Handle rubric file upload
    if (rubricUpload) {
        rubricUpload.addEventListener('change', async function() {
            const file = this.files[0];
            if (file) {
                // Check file type
                const allowedTypes = ['.txt', '.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'];
                const fileExt = '.' + file.name.split('.').pop().toLowerCase();
                
                if (!allowedTypes.includes(fileExt)) {
                    alert('Please upload a valid file type: TXT, PDF, DOC, DOCX, JPG, JPEG, or PNG');
                    this.value = ''; // Clear the input
                    return;
                }
                
                // Show loading state
                if (rubricFileName) {
                    rubricFileName.textContent = 'Processing file...';
                }
                if (rubricFilePreview) {
                    rubricFilePreview.style.display = 'block';
                }
                
                try {
                    // For TXT files, read directly
                    if (fileExt === '.txt') {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            uploadedRubricContent = e.target.result;
                            if (rubricFileName) {
                                rubricFileName.textContent = file.name;
                            }
                            // Show preview of uploaded content
                            if (rubricPreview) {
                                rubricPreview.textContent = uploadedRubricContent.substring(0, 500) + (uploadedRubricContent.length > 500 ? '...' : '');
                            }
                        };
                        reader.readAsText(file);
                    } else {
                        // For PDF, DOC, DOCX files, send to backend for processing
                        const reader = new FileReader();
                        reader.onload = async function(e) {
                            const base64Data = e.target.result.split(',')[1]; // Remove data URL prefix
                            
                            try {
                                const response = await fetch('/process-rubric', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json'
                                    },
                                    body: JSON.stringify({
                                        file_data: base64Data,
                                        filename: file.name
                                    })
                                });
                                
                                const data = await response.json();
                                
                                if (response.ok) {
                                    uploadedRubricContent = data.rubric_content;
                                    if (rubricFileName) {
                                        rubricFileName.textContent = file.name;
                                    }
                                    // Show preview of uploaded content
                                    if (rubricPreview) {
                                        rubricPreview.textContent = uploadedRubricContent.substring(0, 500) + (uploadedRubricContent.length > 500 ? '...' : '');
                                    }
                                } else {
                                    throw new Error(data.error || 'Failed to process file');
                                }
                            } catch (error) {
                                console.error('Error processing rubric file:', error);
                                alert(`Error processing file: ${error.message}`);
                                uploadedRubricContent = null;
                                if (rubricFilePreview) {
                                    rubricFilePreview.style.display = 'none';
                                }
                            }
                        };
                        reader.readAsDataURL(file);
                    }
                } catch (error) {
                    console.error('Error reading file:', error);
                    alert('Error reading file. Please try again.');
                    uploadedRubricContent = null;
                    if (rubricFilePreview) {
                        rubricFilePreview.style.display = 'none';
                    }
                }
            } else {
                uploadedRubricContent = null;
                if (rubricFilePreview) {
                    rubricFilePreview.style.display = 'none';
                }
                if (rubricPreview) {
                    rubricPreview.textContent = '';
                }
            }
        });
    }

    // Toggle rubric preview
    if (rubricToggle) {
        rubricToggle.addEventListener('click', function() {
            if (rubricPreview.style.display === 'none' || rubricPreview.style.display === '') {
                rubricPreview.style.display = 'block';
                this.textContent = 'Hide Rubric';
            } else {
                rubricPreview.style.display = 'none';
                this.textContent = 'Show Rubric';
            }
        });
    }

    // Handle form submission
    if (gradingForm) {
        gradingForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const assignmentType = assignmentTypeSelect.value;
            let rubricContent;
            const currentTab = getCurrentTab();
            
            // Get rubric content based on selection
            if (rubricSelect.value === 'custom') {
                if (customRubricTextarea) {
                    rubricContent = customRubricTextarea.value.trim();
                    if (!rubricContent) {
                        alert('Please enter a custom rubric.');
                        return;
                    }
                }
            } else if (rubricSelect.value === 'upload') {
                if (!uploadedRubricContent) {
                    alert('Please upload a rubric file.');
                    return;
                }
                rubricContent = uploadedRubricContent;
            } else if (rubricSelect.value.startsWith('custom-')) {
                // Handle custom rubrics from database
                const selectedOption = rubricSelect.options[rubricSelect.selectedIndex];
                rubricContent = selectedOption.dataset.content;
            } else {
                // Handle built-in rubrics
                const selectedOption = rubricSelect.options[rubricSelect.selectedIndex];
                rubricContent = selectedOption.dataset.content;
            }
            
            // Validate form
            if (!assignmentType) {
                alert('Please select an assignment type.');
                return;
            }
            
            if (!rubricContent) {
                alert('Please select or enter a rubric.');
                return;
            }
            
            // Handle different submission types based on active tab
            if (currentTab === 'batch') {
                // Batch processing
                if (!batchUpload.files.length) {
                    alert('Please select files for batch processing.');
                    return;
                }
                
                // Show loading indicator
                loadingIndicator.style.display = 'block';
                
                // Hide previous results
                resultCard.style.display = 'none';
                batchResultsSection.style.display = 'none';
                
                try {
                    const formData = new FormData();
                    formData.append('assignment_type', assignmentType);
                    formData.append('rubric', rubricContent);
                    
                    // Add all selected files
                    Array.from(batchUpload.files).forEach(file => {
                        formData.append('files', file);
                    });
                    
                    // Get assignment name if available
                    const assignmentName = document.getElementById('assignment-name') ? 
                        document.getElementById('assignment-name').value : 'Batch Upload';
                    formData.append('assignment_name', assignmentName);
                    
                    const response = await fetch('/grade-batch-upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    loadingIndicator.style.display = 'none';
                    
                    if (response.ok) {
                        displayBatchResults(data);
                    } else {
                        alert(`Error: ${data.error || 'An unknown error occurred'}`);
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('An error occurred while processing the batch upload. Please try again.');
                    loadingIndicator.style.display = 'none';
                }
            } else {
                // Single submission processing (text or single file)
                const submission = submissionTextarea.value.trim();
                
                if (currentTab === 'text' && !submission) {
                    alert('Please enter a text submission.');
                    return;
                }
                
                if (currentTab === 'file' && !fileUpload.files.length) {
                    alert('Please upload a file.');
                    return;
                }
                
                if (currentTab === 'text' && currentTab === 'file' && !submission && !fileUpload.files.length) {
                    alert('Please enter a submission or upload a file.');
                    return;
                }
                
                // Show loading indicator
                loadingIndicator.style.display = 'block';
                
                // Hide previous results
                resultCard.style.display = 'none';
                batchResultsSection.style.display = 'none';
                
                try {
                    const formData = new FormData();
                    formData.append('assignment_type', assignmentType);
                    formData.append('rubric', rubricContent);
                    
                    // Add text submission if provided
                    if (submission) {
                        formData.append('submission', submission);
                    }
                    
                    // Add file if uploaded
                    if (fileUpload.files.length > 0) {
                        formData.append('file', fileUpload.files[0]);
                    }
                    
                    const response = await fetch('/grade-file-upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    handleResponse(response);
                 } catch (error) {
                     console.error('Error:', error);
                     alert('An error occurred while grading the submission. Please try again.');
                     loadingIndicator.style.display = 'none';
                 }
             }
        });
    }

    // Format structured feedback into HTML
    function formatFeedback(feedbackData) {
        try {
            // Try to parse the feedback if it's a JSON string
            let parsedFeedback = feedbackData;
            if (typeof feedbackData === 'string') {
                try {
                    parsedFeedback = JSON.parse(feedbackData);
                } catch (e) {
                    // If not valid JSON, return the original text with some basic formatting
                    return `<div class="simple-feedback">${feedbackData.replace(/\n/g, '<br>')}</div>`;
                }
            }
            
            // Check if we have student metadata in the structured feedback
            if (parsedFeedback.student_name || parsedFeedback.assignment_title) {
                const metadataHtml = `
                <div class="metadata-container">
                    ${parsedFeedback.student_name ? 
                        `<div class="metadata-item">
                            <div class="metadata-label">Student:</div>
                            <div class="metadata-value">${parsedFeedback.student_name}</div>
                        </div>` : ''}
                    ${parsedFeedback.assignment_title ? 
                        `<div class="metadata-item">
                            <div class="metadata-label">Assignment:</div>
                            <div class="metadata-value">${parsedFeedback.assignment_title}</div>
                        </div>` : ''}
                </div>`;
                
                // Save this for later to prepend to the final HTML
                parsedFeedback._metadataHtml = metadataHtml;
            }
            
            // Format for the new structured JSON format
            if (parsedFeedback.questions && Array.isArray(parsedFeedback.questions)) {
                // Start with metadata if available
                let html = '';
                
                // Add student metadata at the top if available
                if (parsedFeedback.student_name || parsedFeedback.assignment_title) {
                    html += `<div class="student-metadata">
                        <div class="student-info-container">
                            ${parsedFeedback.student_name ? 
                                `<div class="student-name"><strong>Student:</strong> ${parsedFeedback.student_name}</div>` : ''}
                            ${parsedFeedback.assignment_title ? 
                                `<div class="assignment-title"><strong>Assignment:</strong> ${parsedFeedback.assignment_title}</div>` : ''}
                        </div>
                    </div>`;
                } else if (parsedFeedback._metadataHtml) {
                    // Use the pre-generated metadata HTML if available
                    html += `<div class="student-metadata">${parsedFeedback._metadataHtml}</div>`;
                }
                
                html += `
                    <div class="structured-feedback">
                        <div class="score-summary">
                            <div class="score-pill">${parsedFeedback.percentage || parsedFeedback.total_score}</div>
                            <div class="score-detail">${parsedFeedback.total_score}</div>
                        </div>
                        
                        <div class="feedback-sections">`;
                
                // Questions section
                html += `
                    <div class="feedback-section">
                        <h4 class="section-title">Question Analysis</h4>
                        <div class="questions-grid">`;
                        
                parsedFeedback.questions.forEach((q, index) => {
                    const isCorrect = q.is_correct || q.is_satisfactory;
                    const statusClass = isCorrect ? 'correct' : 'incorrect';
                    
                    html += `
                        <div class="question-card ${statusClass}">
                            <div class="question-header">
                                <span class="question-number">Q${q.question_number}</span>
                                <span class="question-score">${q.points_earned}/${q.points_possible}</span>
                            </div>
                            
                            <div class="question-details">`;
                    
                    if (q.student_answer || q.student_response || q.student_selection) {
                        html += `<p><strong>Student Response:</strong> ${q.student_answer || q.student_response || q.student_selection}</p>`;
                    }
                    
                    if (q.correct_answer || q.expected_response) {
                        html += `<p><strong>Expected:</strong> ${q.correct_answer || q.expected_response}</p>`;
                    }
                    
                    if (q.mistakes_identified && q.mistakes_identified.length > 0) {
                        html += `<div class="mistakes">
                            <p><strong>Issues:</strong></p>
                            <ul>`;
                        q.mistakes_identified.forEach(mistake => {
                            html += `<li>${mistake}</li>`;
                        });
                        html += `</ul></div>`;
                    }
                    
                    if (q.partial_credit_given_for && q.partial_credit_given_for.length > 0) {
                        html += `<div class="partial-credit">
                            <p><strong>Credit For:</strong></p>
                            <ul>`;
                        q.partial_credit_given_for.forEach(credit => {
                            html += `<li>${credit}</li>`;
                        });
                        html += `</ul></div>`;
                    }
                    
                    if (q.teacher_comment) {
                        html += `<p class="teacher-note"><strong>Note:</strong> ${q.teacher_comment}</p>`;
                    }
                    
                    html += `</div></div>`;
                });
                
                html += `</div></div>`;
                
                // Overall feedback section
                if (parsedFeedback.overall_feedback) {
                    html += `
                        <div class="feedback-section">
                            <h4 class="section-title">Overall Assessment</h4>
                            <div class="overall-feedback">`;
                    
                    if (parsedFeedback.overall_feedback.strengths && parsedFeedback.overall_feedback.strengths.length > 0) {
                        html += `
                            <div class="feedback-strengths">
                                <h5><i class="fas fa-check-circle"></i> Strengths</h5>
                                <ul>`;
                        parsedFeedback.overall_feedback.strengths.forEach(strength => {
                            html += `<li>${strength}</li>`;
                        });
                        html += `</ul>
                            </div>`;
                    }
                    
                    if (parsedFeedback.overall_feedback.areas_for_improvement && parsedFeedback.overall_feedback.areas_for_improvement.length > 0) {
                        html += `
                            <div class="feedback-improvements">
                                <h5><i class="fas fa-arrow-circle-up"></i> Areas for Improvement</h5>
                                <ul>`;
                        parsedFeedback.overall_feedback.areas_for_improvement.forEach(area => {
                            html += `<li>${area}</li>`;
                        });
                        html += `</ul>
                            </div>`;
                    }
                    
                    if (parsedFeedback.overall_feedback.next_steps) {
                        html += `
                            <div class="feedback-next-steps">
                                <h5><i class="fas fa-forward"></i> Next Steps</h5>
                                <p>${parsedFeedback.overall_feedback.next_steps}</p>
                            </div>`;
                    }
                    
                    html += `</div></div>`;
                }
                
                if (parsedFeedback.grading_notes) {
                    html += `
                        <div class="feedback-section grading-notes">
                            <h5>Notes for Teacher</h5>
                            <p>${parsedFeedback.grading_notes}</p>
                        </div>`;
                }
                
                html += `</div></div>`;
                
                return html;
            }
            
            // Fallback for simple feedback structure
            let html = '';
            
            // Add student metadata at the top if available
            if (parsedFeedback.student_name || parsedFeedback.assignment_title) {
                html += `<div class="student-metadata">
                    <div class="student-info-container">
                        ${parsedFeedback.student_name ? 
                            `<div class="student-name"><strong>Student:</strong> ${parsedFeedback.student_name}</div>` : ''}
                        ${parsedFeedback.assignment_title ? 
                            `<div class="assignment-title"><strong>Assignment:</strong> ${parsedFeedback.assignment_title}</div>` : ''}
                    </div>
                </div>`;
            } else if (parsedFeedback._metadataHtml) {
                // Use the pre-generated metadata HTML if available
                html += `<div class="student-metadata">${parsedFeedback._metadataHtml}</div>`;
            }
            
            // Add the feedback content
            html += `<div class="simple-feedback">${typeof parsedFeedback === 'string' ? 
                parsedFeedback.replace(/\n/g, '<br>') : 
                JSON.stringify(parsedFeedback, null, 2).replace(/\n/g, '<br>').replace(/ /g, '&nbsp;')
            }</div>`;
            
            return html;
            
        } catch (error) {
            console.error('Error formatting feedback:', error);
            return `<div class="simple-feedback">${feedbackData.replace(/\n/g, '<br>')}</div>`;
        }
    }

    // Handle API response
    async function handleResponse(response) {
        const data = await response.json();
        
        // Hide loading indicator
        loadingIndicator.style.display = 'none';
        
        if (response.ok) {
            // Display results
            scoreDisplay.textContent = data.score;
            
            // Try to format the feedback if it appears to be structured
            try {
                // Check if we're receiving structured JSON directly from the server
                if (typeof data.feedback === 'object' && data.feedback !== null) {
                    console.log('Received structured feedback object:', data.feedback);
                    feedbackDisplay.innerHTML = formatFeedback(data.feedback);
                } else {
                    // Try to parse it as JSON if it's a string (legacy format)
                    console.log('Received feedback string, attempting to format:', data.feedback);
                    feedbackDisplay.innerHTML = formatFeedback(data.feedback);
                }
            } catch (e) {
                console.error('Error formatting feedback:', e);
                // Fallback to plain text display
                feedbackDisplay.textContent = typeof data.feedback === 'object' ? 
                    JSON.stringify(data.feedback, null, 2) : data.feedback;
            }
            
            // Display student name and assignment title if available
            // Create a dedicated prominent section for student metadata
            const metadataContainer = document.createElement('div');
            metadataContainer.className = 'metadata-container';
            resultCard.insertBefore(metadataContainer, resultCard.firstChild);
            
            let studentName = null;
            let assignmentTitle = null;
            
            // Enhanced extraction of student name from multiple possible sources
            console.log("Attempting to extract student name from response:", data);
            
            // Source 1: Direct metadata from OCR extraction
            if (data.student_name_info && data.student_name_info.student_name) {
                console.log("Found student name in student_name_info:", data.student_name_info.student_name);
                studentName = data.student_name_info.student_name;
            } 
            // Source 2: From feedback object
            else if (typeof data.feedback === 'object' && data.feedback.student_name) {
                console.log("Found student name in feedback object:", data.feedback.student_name);
                studentName = data.feedback.student_name;
            }
            // Source 3: From formatted feedback (string format)
            else if (typeof data.feedback === 'string' && data.feedback.includes("**STUDENT:")) {
                const match = data.feedback.match(/\*\*STUDENT:\s*([^\*\n]+)\*\*/);
                if (match && match[1] && match[1] !== "[Name not detected]") {
                    console.log("Found student name in formatted feedback string:", match[1].trim());
                    studentName = match[1].trim();
                }
            }
            // Source 4: From extracted text (OCR output)
            else if (data.extracted_text && data.extracted_text.includes("**STUDENT:")) {
                const match = data.extracted_text.match(/\*\*STUDENT:\s*([^\*\n]+)\*\*/);
                if (match && match[1] && match[1] !== "[Name not detected]") {
                    console.log("Found student name in extracted text:", match[1].trim());
                    studentName = match[1].trim();
                }
            }
            // Source 5: From formatted_feedback if available
            else if (data.formatted_feedback && typeof data.formatted_feedback === 'string' && data.formatted_feedback.includes("**STUDENT:")) {
                const match = data.formatted_feedback.match(/\*\*STUDENT:\s*([^\*\n]+)\*\*/);
                if (match && match[1] && match[1] !== "[Name not detected]") {
                    console.log("Found student name in formatted_feedback:", match[1].trim());
                    studentName = match[1].trim();
                }
            }
            
            // Clean up student name if found
            if (studentName) {
                studentName = studentName.replace(/\[|\]/g, '').trim();
                if (studentName.toLowerCase() === "name not detected") {
                    studentName = null;
                }
            }
            
            // Similar enhanced extraction for assignment title
            if (data.assignment_title_info && data.assignment_title_info.assignment_title) {
                console.log("Found assignment title in assignment_title_info:", data.assignment_title_info.assignment_title);
                assignmentTitle = data.assignment_title_info.assignment_title;
            } else if (typeof data.feedback === 'object' && data.feedback.assignment_title) {
                console.log("Found assignment title in feedback object:", data.feedback.assignment_title);
                assignmentTitle = data.feedback.assignment_title;
            } else if (typeof data.feedback === 'string' && data.feedback.includes("**ASSIGNMENT:")) {
                const match = data.feedback.match(/\*\*ASSIGNMENT:\s*([^\*\n]+)\*\*/);
                if (match && match[1] && match[1] !== "[Title not detected]") {
                    console.log("Found assignment title in formatted feedback string:", match[1].trim());
                    assignmentTitle = match[1].trim();
                }
            } else if (data.extracted_text && data.extracted_text.includes("**ASSIGNMENT:")) {
                const match = data.extracted_text.match(/\*\*ASSIGNMENT:\s*([^\*\n]+)\*\*/);
                if (match && match[1] && match[1] !== "[Title not detected]") {
                    console.log("Found assignment title in extracted text:", match[1].trim());
                    assignmentTitle = match[1].trim();
                }
            } else if (data.formatted_feedback && typeof data.formatted_feedback === 'string' && data.formatted_feedback.includes("**ASSIGNMENT:")) {
                const match = data.formatted_feedback.match(/\*\*ASSIGNMENT:\s*([^\*\n]+)\*\*/);
                if (match && match[1] && match[1] !== "[Title not detected]") {
                    console.log("Found assignment title in formatted_feedback:", match[1].trim());
                    assignmentTitle = match[1].trim();
                }
            }
            
            // Clean up assignment title if found
            if (assignmentTitle) {
                assignmentTitle = assignmentTitle.replace(/\[|\]/g, '').trim();
                if (assignmentTitle.toLowerCase() === "title not detected") {
                    assignmentTitle = null;
                }
            }
            
            // Always display metadata section, even with placeholders
            let metadataHtml = '';
            
            metadataHtml += `
                <div class="student-metadata" id="student-info-panel">
                    <h3 class="metadata-header">Submission Information</h3>
                    <div class="student-info-container">
                        <div class="metadata-item">
                            <div class="metadata-label">Student:</div>
                            <div class="metadata-value" id="student-name-value">${studentName || 'Not detected'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Assignment:</div>
                            <div class="metadata-value" id="assignment-title-value">${assignmentTitle || 'Not detected'}</div>
                        </div>
                    </div>
                </div>
            `;
            
            metadataContainer.innerHTML = metadataHtml;
            
            // Add student name to window for debugging
            window.lastGradedStudentName = studentName;
            window.lastGradedAssignmentTitle = assignmentTitle;
            console.log("Final extracted student name:", studentName);
            console.log("Final extracted assignment title:", assignmentTitle);
            
            // Save metadata in the feedback object for other components to use
            if (typeof data.feedback === 'object') {
                data.feedback.student_name = studentName;
                data.feedback.assignment_title = assignmentTitle;
            }
            
            // Show extracted text if available
            if (data.extracted_text) {
                extractedText.textContent = data.extracted_text;
                extractedTextSection.style.display = 'block';
            } else {
                extractedTextSection.style.display = 'none';
            }
            
            // Show result card
            resultCard.style.display = 'block';
            
            // Scroll to results
            resultCard.scrollIntoView({ behavior: 'smooth' });
        } else {
            // Check for specific error types
            if (data.error === "Tesseract OCR is not installed") {
                // Create a more user-friendly error message for Tesseract not installed
                const errorMessage = `${data.error}: ${data.details || ''}`;
                
                // Display error in the result card instead of an alert
                scoreDisplay.textContent = "Error";
                feedbackDisplay.innerHTML = `<div class="alert alert-danger">
                    <strong>Image Processing Error:</strong><br>
                    ${errorMessage}<br><br>
                    <p>Please use text submission instead of image upload until this is resolved.</p>
                </div>`;
                
                // Show result card with error
                resultCard.style.display = 'block';
                extractedTextSection.style.display = 'none';
                
                // Scroll to results
                resultCard.scrollIntoView({ behavior: 'smooth' });
            } else {
                // For other errors, use the standard alert
                alert(`Error: ${data.error || 'An unknown error occurred'}`);
            }
        }
    }
    
    // Helper function to format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Helper function to remove file from batch
    function removeFileFromBatch(index) {
        const dt = new DataTransfer();
        const files = Array.from(batchUpload.files);
        
        files.forEach((file, i) => {
            if (i !== index) {
                dt.items.add(file);
            }
        });
        
        batchUpload.files = dt.files;
        
        // Trigger change event to update UI
        batchUpload.dispatchEvent(new Event('change'));
    }
    
    // Helper function to get current tab
    function getCurrentTab() {
        const activeTab = document.querySelector('.tab.active');
        return activeTab ? activeTab.dataset.tab : 'text';
    }
    
    // Handle batch results display
    function displayBatchResults(data) {
        const { results, summary } = data;
        
        // Hide single result section
        resultCard.style.display = 'none';
        
        // Update summary
        let excelDownloadHtml = '';
        
        // Check if Excel export is available
        if (data.excel_export && data.excel_export.url) {
            excelDownloadHtml = `
                <div class="excel-download">
                    <a href="${data.excel_export.url}" class="excel-download-btn" download>
                        <i class="fas fa-file-excel"></i> Download Excel Report
                    </a>
                </div>
            `;
        }
        
        batchSummary.innerHTML = `
            <div class="summary-stats">
                <div class="stat">
                    <span class="stat-number">${summary.total_files}</span>
                    <span class="stat-label">Total Files</span>
                </div>
                <div class="stat">
                    <span class="stat-number">${summary.processed}</span>
                    <span class="stat-label">Processed</span>
                </div>
                <div class="stat">
                    <span class="stat-number">${summary.failed}</span>
                    <span class="stat-label">Failed</span>
                </div>
                <div class="stat">
                    <span class="stat-number">${summary.average_score}</span>
                    <span class="stat-label">Avg Score</span>
                </div>
            </div>
            ${excelDownloadHtml}
        `;
        
        // Clear previous results
        batchResultsContent.innerHTML = '';
        
        // Display individual results
        results.forEach((result, index) => {
            const resultItem = document.createElement('div');
            resultItem.className = 'batch-result-item';
            
            if (result.error) {
                resultItem.innerHTML = `
                    <div class="result-header error">
                        <h3 class="result-filename">${result.filename}</h3>
                        <div class="result-status error">
                            <i class="fas fa-exclamation-triangle"></i>
                            Error
                        </div>
                    </div>
                    <div class="result-content">
                        <div class="error-message">
                            <strong>Error:</strong> ${result.error}<br>
                            <small>${result.details || ''}</small>
                        </div>
                    </div>
                `;
            } else {
                resultItem.innerHTML = `
                    <div class="result-header">
                        <h3 class="result-filename">${result.filename}</h3>
                        <div class="result-score">${result.score}</div>
                    </div>
                    <div class="result-content">
                        <div class="result-feedback">
                            <h4>Feedback</h4>
                            <p>${result.feedback}</p>
                        </div>
                        <div class="result-extracted" style="display: ${result.extracted_text ? 'block' : 'none'}">
                            <h4>Extracted Text</h4>
                            <div class="extracted-preview">
                                ${result.extracted_text ? result.extracted_text.substring(0, 200) + (result.extracted_text.length > 200 ? '...' : '') : ''}
                            </div>
                            ${result.extracted_text && result.extracted_text.length > 200 ? 
                                `<button class="show-full-text" data-index="${index}">Show Full Text</button>` : ''}
                        </div>
                    </div>
                `;
            }
            
            batchResultsContent.appendChild(resultItem);
        });
        
        // Add event listeners for "Show Full Text" buttons
        batchResultsContent.querySelectorAll('.show-full-text').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                const extractedDiv = this.parentElement.querySelector('.extracted-preview');
                const result = results[index];
                
                if (this.textContent === 'Show Full Text') {
                    extractedDiv.textContent = result.extracted_text;
                    this.textContent = 'Show Less';
                } else {
                    extractedDiv.innerHTML = result.extracted_text.substring(0, 200) + (result.extracted_text.length > 200 ? '...' : '');
                    this.textContent = 'Show Full Text';
                }
            });
        });
        
        // Show batch results section
        batchResultsSection.style.display = 'block';
        
        // Scroll to results
        batchResultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Extension functionality
    function showComingSoonModal() {
        // Create modal overlay
        const modalOverlay = document.createElement('div');
        modalOverlay.className = 'modal-overlay';
        modalOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        `;
        
        // Create modal content
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';
        modalContent.style.cssText = `
            background: white;
            padding: 2rem;
            border-radius: 12px;
            text-align: center;
            max-width: 400px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        `;
        
        modalContent.innerHTML = `
             <h2 style="color: var(--text-primary); margin-bottom: 1rem;">Coming Soon...</h2>
            <p style="color: var(--text-secondary); margin-bottom: 2rem;">The SnapGrade Chrome Extension is currently in development. Stay tuned for an amazing grading experience!</p>
            <button id="close-modal" style="
                background: var(--primary-blue);
                color: white;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            ">Got it!</button>
        `;
        
        modalOverlay.appendChild(modalContent);
        document.body.appendChild(modalOverlay);
        
        // Close modal functionality
        function closeModal() {
            document.body.removeChild(modalOverlay);
        }
        
        modalOverlay.addEventListener('click', function(e) {
            if (e.target === modalOverlay) {
                closeModal();
            }
        });
        
        document.getElementById('close-modal').addEventListener('click', closeModal);
        
        // Close on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeModal();
            }
        });
    }
    
    // Add event listeners for extension-related elements
    
    // Extension menu item in sidebar
    const extensionMenuItem = document.querySelector('.nav-item:nth-child(2)');
    if (extensionMenuItem && extensionMenuItem.textContent.includes('Extension')) {
        extensionMenuItem.addEventListener('click', function(e) {
            e.preventDefault();
            showComingSoonModal();
        });
        extensionMenuItem.style.cursor = 'pointer';
    }
    
    // Get Extension button in banner
    const getExtensionBtn = document.querySelector('.get-extension-btn');
    if (getExtensionBtn) {
        getExtensionBtn.addEventListener('click', function(e) {
            e.preventDefault();
            showComingSoonModal();
        });
    }
    
    // Workflow card action buttons (extension-related)
    const workflowCards = document.querySelectorAll('.workflow-card');
    workflowCards.forEach(card => {
        const cardText = card.textContent.toLowerCase();
        if (cardText.includes('extension') || cardText.includes('google docs') || cardText.includes('canvas')) {
            const actionBtn = card.querySelector('.card-action-btn');
            if (actionBtn) {
                actionBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    showComingSoonModal();
                });
            }
        }
    });
    
    // Add event listener for Help tab
    const helpNavItems = document.querySelectorAll('.nav-item');
    let helpNavItem = null;
    helpNavItems.forEach(item => {
        const span = item.querySelector('span');
        if (span && span.textContent.trim() === 'Help') {
            helpNavItem = item;
            item.addEventListener('click', function(e) {
                e.preventDefault();
                showHelpPage();
            });
            item.style.cursor = 'pointer';
        }
    });
    
    // Add event listener for contact form
        const contactForm = document.getElementById('contact-form');
        if (contactForm) {
            contactForm.addEventListener('submit', handleContactForm);
        }
        
        // Initialize drag-and-drop for rubric upload
function initializeRubricDropZone() {
    const rubricDropZone = document.getElementById('rubric-drop-zone');
    const rubricUpload = document.getElementById('rubric-upload');
    
    if (!rubricDropZone || !rubricUpload) return;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        rubricDropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        rubricDropZone.addEventListener(eventName, () => highlight(rubricDropZone), false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        rubricDropZone.addEventListener(eventName, () => unhighlight(rubricDropZone), false);
    });
    
    // Handle dropped files
    rubricDropZone.addEventListener('drop', handleRubricDrop, false);
}

// Handle rubric file drop
function handleRubricDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        const file = files[0];
        const allowedTypes = ['.txt', '.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (allowedTypes.includes(fileExtension)) {
            const rubricUpload = document.getElementById('rubric-upload');
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            rubricUpload.files = dataTransfer.files;
            
            // Trigger the change event to update UI
            const event = new Event('change', { bubbles: true });
            rubricUpload.dispatchEvent(event);
            
            // Update preview
            updateRubricPreview(file);
        } else {
            alert('Please upload a valid rubric file (TXT, PDF, DOC, DOCX, JPG, JPEG, PNG)');
        }
    }
}

// Update rubric file preview
function updateRubricPreview(file) {
    const preview = document.getElementById('rubric-file-preview');
    const fileName = document.getElementById('rubric-file-name');
    const uploadText = document.querySelector('#rubric-drop-zone .upload-text');
    
    if (preview && fileName && uploadText) {
        fileName.textContent = file.name;
        preview.style.display = 'block';
        uploadText.textContent = 'Rubric file selected';
    }
}

// Update single file preview
function updateSingleFilePreview(file) {
    const preview = document.getElementById('file-preview');
    const fileName = document.getElementById('file-name');
    const uploadText = document.querySelector('#single-file-drop-zone .upload-text');
    
    if (preview && fileName && uploadText) {
        fileName.textContent = file.name;
        preview.style.display = 'block';
        uploadText.textContent = 'Assignment file selected';
    }
}

// Add remove file functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize drag-and-drop zones
    initializeSingleFileDropZone();
    initializeRubricDropZone();
    
    // Remove single file
    const removeSingleFile = document.getElementById('remove-file');
    if (removeSingleFile) {
        removeSingleFile.addEventListener('click', function() {
            const fileUpload = document.getElementById('file-upload');
            const preview = document.getElementById('file-preview');
            const uploadText = document.querySelector('#single-file-drop-zone .upload-text');
            
            if (fileUpload) fileUpload.value = '';
            if (preview) preview.style.display = 'none';
            if (uploadText) uploadText.textContent = 'Click to upload or drag & drop assignment';
        });
    }
    
    // Remove rubric file
    const removeRubricFile = document.getElementById('remove-rubric-file');
    if (removeRubricFile) {
        removeRubricFile.addEventListener('click', function() {
            const rubricUpload = document.getElementById('rubric-upload');
            const preview = document.getElementById('rubric-file-preview');
            const uploadText = document.querySelector('#rubric-drop-zone .upload-text');
            
            if (rubricUpload) rubricUpload.value = '';
            if (preview) preview.style.display = 'none';
            if (uploadText) uploadText.textContent = 'Click to upload or drag & drop rubric';
        });
    }
});

// Add event listeners for rubric actions
        document.addEventListener('click', function(e) {
            // Create new rubric button
            if (e.target.closest('.create-rubric-btn')) {
                showCreateRubricModal();
            }
            
            // Edit rubric button
            if (e.target.closest('.edit-btn')) {
                const rubricCard = e.target.closest('.rubric-card');
                const rubricName = rubricCard.querySelector('h3').textContent;
                alert(`Edit "${rubricName}" functionality coming soon!`);
            }
            
            // Delete rubric button
            if (e.target.closest('.delete-btn')) {
                const rubricCard = e.target.closest('.rubric-card');
                if (rubricCard) {
                    const rubricName = rubricCard.querySelector('h3').textContent;
                    if (confirm(`Are you sure you want to delete "${rubricName}"?`)) {
                        rubricCard.remove();
                    }
                } else {
                    // Handle class card deletion
                    const classCard = e.target.closest('.class-card');
                    if (classCard) {
                        const className = classCard.querySelector('h3').textContent;
                        if (confirm(`Are you sure you want to delete "${className}"?`)) {
                            classCard.remove();
                        }
                    }
                }
            }
            
            // Create new class button - handled by onclick in HTML
            
            // Edit class button - functionality available through class actions
        });
        
        // Add event listener for Grade/Rubrics nav item to show rubrics page
        const gradeNavItems = document.querySelectorAll('.nav-item');
        gradeNavItems.forEach(item => {
            const span = item.querySelector('span');
            if (span && span.textContent.trim() === 'Rubrics') {
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    showRubricsPage();
                });
                item.style.cursor = 'pointer';
            }
            if (span && span.textContent.trim() === 'Classes') {
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    showClassesPage();
                });
                item.style.cursor = 'pointer';
            }
        });
        
        // Add event listener for Start Guide nav item to go back to homepage
         const startGuideNavItems = document.querySelectorAll('.nav-item');
         startGuideNavItems.forEach(item => {
             const span = item.querySelector('span');
             if (span && span.textContent.trim() === 'Start Guide') {
                 item.addEventListener('click', function(e) {
                     e.preventDefault();
                     showGradePage();
                 });
                 item.style.cursor = 'pointer';
             }
         });
    
    // Helper function to show rubrics page
      function showRubricsPage() {
          // Hide other content sections
          const gradePage = document.getElementById('grade-page');
          const helpSection = document.getElementById('help-page');
          const classesSection = document.getElementById('classes-page');
          const batchResultsSection = document.getElementById('batch-results-section');
          const resultCard = document.getElementById('results-section');
          
          if (gradePage) gradePage.style.display = 'none';
          if (helpSection) helpSection.style.display = 'none';
          if (classesSection) classesSection.style.display = 'none';
          if (batchResultsSection) batchResultsSection.style.display = 'none';
          if (resultCard) resultCard.style.display = 'none';
          
          // Show rubrics section
        const rubricsSection = document.getElementById('rubrics-page');
        if (rubricsSection) {
            rubricsSection.style.display = 'block';
        }
        
        // Load rubrics when showing the page
        loadRubrics();
          
          // Update active nav item
          document.querySelectorAll('.nav-item').forEach(item => {
              item.classList.remove('active');
              const span = item.querySelector('span');
              if (span && span.textContent.trim() === 'Rubrics') {
                  item.classList.add('active');
              }
          });
      }
      
      // Helper function to show classes page
      function showClassesPage() {
          // Hide other content sections
          const gradePage = document.getElementById('grade-page');
          const helpSection = document.getElementById('help-page');
          const rubricsSection = document.getElementById('rubrics-page');
          const batchResultsSection = document.getElementById('batch-results-section');
          const resultCard = document.getElementById('results-section');
          
          if (gradePage) gradePage.style.display = 'none';
          if (helpSection) helpSection.style.display = 'none';
          if (rubricsSection) rubricsSection.style.display = 'none';
          if (batchResultsSection) batchResultsSection.style.display = 'none';
          if (resultCard) resultCard.style.display = 'none';
          
          // Show classes section
          const classesSection = document.getElementById('classes-page');
          if (classesSection) {
              classesSection.style.display = 'block';
          }
          
          // Update active nav item
          document.querySelectorAll('.nav-item').forEach(item => {
              item.classList.remove('active');
              const span = item.querySelector('span');
              if (span && span.textContent.trim() === 'Classes') {
                  item.classList.add('active');
              }
          });
          
          // Load classes when page is shown
          loadClasses();
      }
      
      // Helper function to show help page
     function showHelpPage() {
         // Hide main content sections
         const gradePage = document.getElementById('grade-page');
         const rubricsSection = document.getElementById('rubrics-page');
         const classesSection = document.getElementById('classes-page');
         const batchResultsSection = document.getElementById('batch-results-section');
         const resultCard = document.getElementById('results-section');
         
         if (gradePage) gradePage.style.display = 'none';
         if (rubricsSection) rubricsSection.style.display = 'none';
         if (classesSection) classesSection.style.display = 'none';
         if (batchResultsSection) batchResultsSection.style.display = 'none';
         if (resultCard) resultCard.style.display = 'none';
         
         // Show help section
         const helpSection = document.getElementById('help-page');
         if (helpSection) {
             helpSection.style.display = 'block';
         }
         
         // Update active nav item
         document.querySelectorAll('.nav-item').forEach(item => {
             item.classList.remove('active');
         });
         if (helpNavItem) {
             helpNavItem.classList.add('active');
         }
     }
     
     // Helper function to show grade page
      function showGradePage() {
          // Hide all other sections
          const helpSection = document.getElementById('help-page');
          const rubricsSection = document.getElementById('rubrics-page');
          const classesSection = document.getElementById('classes-page');
          const batchResultsSection = document.getElementById('batch-results-section');
          const resultCard = document.getElementById('results-section');
          
          if (helpSection) helpSection.style.display = 'none';
          if (rubricsSection) rubricsSection.style.display = 'none';
          if (classesSection) classesSection.style.display = 'none';
          if (batchResultsSection) batchResultsSection.style.display = 'none';
          if (resultCard) resultCard.style.display = 'none';
          
          // Show main grading content
          const gradePage = document.getElementById('grade-page');
          if (gradePage) {
              gradePage.style.display = 'flex';
          }
          
          // Update active nav item - no specific item should be active for main page
          document.querySelectorAll('.nav-item').forEach(item => {
              item.classList.remove('active');
          });
      }
      
      // Helper function to handle contact form submission
      async function handleContactForm(e) {
          e.preventDefault();
          
          const name = document.getElementById('contact-name').value;
          const email = document.getElementById('contact-email').value;
          const subject = document.getElementById('contact-subject').value;
          const message = document.getElementById('contact-message').value;
          
          // Simple validation
          if (!name || !email || !subject || !message) {
              alert('Please fill in all required fields.');
              return;
          }
          
          // Show loading state
          const submitBtn = e.target.querySelector('.submit-btn');
          const originalText = submitBtn.innerHTML;
          submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
          submitBtn.disabled = true;
          
          try {
              // Send form data to server
              const response = await fetch('/contact', {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({
                      name: name,
                      email: email,
                      subject: subject,
                      message: message
                  })
              });
              
              const data = await response.json();
              
              if (data.success) {
                  alert(data.message);
                  e.target.reset();
              } else {
                  alert('Error: ' + (data.error || 'Failed to send message'));
              }
          } catch (error) {
              console.error('Error sending contact form:', error);
              alert('Failed to send message. Please try again later.');
          } finally {
              // Restore button state
              submitBtn.innerHTML = originalText;
              submitBtn.disabled = false;
          }
      }
});

// Rubric Management Functions

// Load rubrics from backend
async function loadRubrics() {
    try {
        const response = await fetch('/rubrics');
        if (response.ok) {
            loadedRubrics = await response.json();
            displayRubrics();
        } else {
            console.error('Failed to load rubrics');
        }
    } catch (error) {
        console.error('Error loading rubrics:', error);
    }
}

// Display rubrics in the UI
function displayRubrics() {
    const rubricsGrid = document.querySelector('.rubrics-grid');
    const rubricsEmpty = document.querySelector('.rubrics-empty');
    
    if (!rubricsGrid) return;
    
    // Clear existing rubrics (keep the sample ones)
    const existingCustomRubrics = rubricsGrid.querySelectorAll('.rubric-card[data-custom="true"]');
    existingCustomRubrics.forEach(card => card.remove());
    
    if (loadedRubrics.length === 0) {
        if (rubricsEmpty) rubricsEmpty.style.display = 'block';
        return;
    }
    
    if (rubricsEmpty) rubricsEmpty.style.display = 'none';
    
    loadedRubrics.forEach(rubric => {
        const rubricCard = document.createElement('div');
        rubricCard.className = 'rubric-card';
        rubricCard.setAttribute('data-custom', 'true');
        rubricCard.innerHTML = `
            <div class="rubric-actions">
                <button class="edit-btn" title="Edit Rubric">✏️</button>
                <button class="delete-btn" title="Delete Rubric" data-rubric-id="${rubric.id}">🗑️</button>
            </div>
            <h3>${rubric.name}</h3>
            <p class="rubric-description">${rubric.description}</p>
            <div class="rubric-meta">
                <span class="rubric-type">${rubric.type}</span>
                <span class="rubric-date">Created: ${new Date(rubric.created_at).toLocaleDateString()}</span>
            </div>
        `;
        rubricsGrid.appendChild(rubricCard);
    });
}

// Show create rubric modal
function showCreateRubricModal() {
    const modal = document.getElementById('create-rubric-modal');
    if (modal) {
        modal.style.display = 'flex';
        // Clear form
        const form = modal.querySelector('form');
        if (form) form.reset();
    }
}

// Hide create rubric modal
function hideCreateRubricModal() {
    const modal = document.getElementById('create-rubric-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Handle create rubric form submission
async function handleCreateRubric(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const rubricData = {
        name: formData.get('name'),
        type: formData.get('type'),
        description: formData.get('description'),
        content: formData.get('content')
    };
    
    try {
        const response = await fetch('/rubrics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(rubricData)
        });
        
        if (response.ok) {
            const result = await response.json();
            alert('Rubric created successfully!');
            hideCreateRubricModal();
            loadRubrics(); // Reload rubrics
        } else {
            const error = await response.json();
            alert('Error: ' + (error.error || 'Failed to create rubric'));
        }
    } catch (error) {
        console.error('Error creating rubric:', error);
        alert('Failed to create rubric. Please try again.');
    }
}

// Delete rubric
async function deleteRubric(rubricId) {
    if (!confirm('Are you sure you want to delete this rubric?')) {
        return;
    }
    
    try {
        const response = await fetch(`/rubrics/${rubricId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('Rubric deleted successfully!');
            loadRubrics(); // Reload rubrics
        } else {
            const error = await response.json();
            alert('Error: ' + (error.error || 'Failed to delete rubric'));
        }
    } catch (error) {
        console.error('Error deleting rubric:', error);
        alert('Failed to delete class. Please try again.');
    }
}
window.deleteClass = deleteClass;

// Event listeners for rubric modal
document.addEventListener('DOMContentLoaded', function() {
    // Modal close button
    const closeBtn = document.querySelector('#create-rubric-modal .close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', hideCreateRubricModal);
    }
    
    // Modal cancel button
    const cancelBtn = document.querySelector('#create-rubric-modal .cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', hideCreateRubricModal);
    }
    
    // Modal form submission
    const createRubricForm = document.querySelector('#create-rubric-modal form');
    if (createRubricForm) {
        createRubricForm.addEventListener('submit', handleCreateRubric);
    }
    
    // Click outside modal to close
    const modal = document.getElementById('create-rubric-modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                hideCreateRubricModal();
            }
        });
    }
    
    // Delete rubric buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-btn')) {
            const rubricId = e.target.closest('.delete-btn').getAttribute('data-rubric-id');
            if (rubricId) {
                deleteRubric(rubricId);
            }
        }
    });
});

// Class Management Functions
let loadedClasses = [];
let currentClassId = null;
let currentStudents = [];

// Load classes from backend
async function loadClasses() {
    try {
        const response = await fetch('/classes');
        if (response.ok) {
            loadedClasses = await response.json();
            displayClasses();
        } else {
            console.error('Failed to load classes');
        }
    } catch (error) {
        console.error('Error loading classes:', error);
    }
}

// Display classes in the UI
function displayClasses() {
    const classesGrid = document.querySelector('.classes-grid');
    if (!classesGrid) return;
    
    // Clear existing custom classes (keep sample ones)
    const existingCustomClasses = classesGrid.querySelectorAll('.class-card[data-custom="true"]');
    existingCustomClasses.forEach(card => card.remove());
    
    if (loadedClasses.length === 0) {
        return;
    }
    
    // Add custom classes
    loadedClasses.forEach(classData => {
        const classCard = document.createElement('div');
        classCard.className = 'class-card';
        classCard.setAttribute('data-custom', 'true');
        classCard.setAttribute('data-class-id', classData.id);
        
        classCard.innerHTML = `
            <div class="class-header">
                <h3>${classData.name}</h3>
                <div class="class-actions">
                    <button class="action-btn edit-btn" onclick="editClass('${classData.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="action-btn delete-btn" onclick="deleteClass('${classData.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="class-info">
                <p class="class-description">${classData.description}</p>
                <div class="class-details">
                    <span class="class-period">Period: ${classData.period}</span>
                    <span class="class-semester">${classData.semester}</span>
                </div>
                <div class="class-stats">
                    <span class="stat-item">
                        <i class="fas fa-users"></i>
                        ${classData.student_count} Students
                    </span>
                    <span class="stat-item">
                        <i class="fas fa-file-alt"></i>
                        ${classData.assignment_count} Assignments
                    </span>
                    <span class="stat-item">
                        <i class="fas fa-check-circle"></i>
                        ${classData.graded_count} Graded
                    </span>
                </div>
                <div class="class-actions-bottom">
                    <button class="btn btn-primary" onclick="manageStudents('${classData.id}')">
                        <i class="fas fa-users"></i> Manage Students
                    </button>
                    <button class="btn btn-secondary" onclick="submitBatchAssignment('${classData.id}')">
                        <i class="fas fa-upload"></i> Submit Assignment
                    </button>
                    <button class="btn btn-info" onclick="viewClassGrades('${classData.id}')">
                        <i class="fas fa-chart-bar"></i> View Grades
                    </button>
                </div>
            </div>
        `;
        
        classesGrid.appendChild(classCard);
    });
}

// Show create class modal
function showCreateClassModal() {
    console.log('showCreateClassModal called');
    const modal = document.getElementById('create-class-modal');
    console.log('Modal element:', modal);
    if (modal) {
        modal.style.display = 'flex';
        console.log('Modal display set to flex');
        // Clear form
        const form = modal.querySelector('form');
        if (form) form.reset();
    } else {
        console.error('Modal not found!');
    }
}

// Make functions globally accessible
window.showCreateClassModal = showCreateClassModal;

// Hide create class modal
function hideCreateClassModal() {
    const modal = document.getElementById('create-class-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}
window.hideCreateClassModal = hideCreateClassModal;

// Handle create class form submission
async function handleCreateClass(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const classData = {
        name: formData.get('name'),
        description: formData.get('description'),
        period: formData.get('period'),
        semester: formData.get('semester')
    };
    
    try {
        const response = await fetch('/classes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(classData)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            alert('Class created successfully!');
            hideCreateClassModal();
            loadClasses(); // Reload classes
        } else {
            alert(result.error || 'Failed to create class');
        }
    } catch (error) {
        console.error('Error creating class:', error);
        alert('Error creating class. Please try again.');
    }
}
window.handleCreateClass = handleCreateClass;

// Edit class function
function editClass(classId) {
    // For now, show a simple alert - can be expanded to show edit modal
    alert('Edit class functionality - you can expand this to show an edit modal');
}
window.editClass = editClass;

// Delete class
async function deleteClass(classId) {
    if (!confirm('Are you sure you want to delete this class? This will also delete all associated students and grades.')) {
        return;
    }
    
    try {
        const response = await fetch(`/classes/${classId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            alert('Class deleted successfully!');
            loadClasses(); // Reload classes
        } else {
            alert(result.error || 'Failed to delete class');
        }
    } catch (error) {
        console.error('Error deleting class:', error);
        alert('Error deleting class. Please try again.');
    }
}
window.deleteClass = deleteClass;

// Manage students in a class
async function manageStudents(classId) {
    currentClassId = classId;
    
    // Load students for this class
    try {
        const response = await fetch(`/classes/${classId}/students`);
        if (response.ok) {
            currentStudents = await response.json();
            showStudentManagementModal();
        } else {
            alert('Failed to load students');
        }
    } catch (error) {
        console.error('Error loading students:', error);
        alert('Error loading students');
    }
}
window.manageStudents = manageStudents;

// Show student management modal
function showStudentManagementModal() {
    const modal = document.getElementById('student-management-modal');
    if (modal) {
        modal.style.display = 'flex';
        displayStudentsInModal();
    }
}
window.showStudentManagementModal = showStudentManagementModal;

// Hide student management modal
function hideStudentManagementModal() {
    const modal = document.getElementById('student-management-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}
window.hideStudentManagementModal = hideStudentManagementModal;

// Display students in the modal
function displayStudentsInModal() {
    const studentsList = document.getElementById('students-list');
    if (!studentsList) return;
    
    studentsList.innerHTML = '';
    
    if (currentStudents.length === 0) {
        studentsList.innerHTML = '<p class="no-students">No students enrolled in this class.</p>';
        return;
    }
    
    currentStudents.forEach(student => {
        const studentItem = document.createElement('div');
        studentItem.className = 'student-item';
        studentItem.innerHTML = `
            <div class="student-info">
                <h4>${student.name}</h4>
                <p>${student.email}</p>
                ${student.student_id ? `<p>ID: ${student.student_id}</p>` : ''}
            </div>
            <div class="student-actions">
                <button class="btn btn-danger btn-sm" onclick="deleteStudent('${student.id}')">
                    <i class="fas fa-trash"></i> Remove
                </button>
                <button class="btn btn-info btn-sm" onclick="viewStudentGrades('${student.id}')">
                    <i class="fas fa-chart-line"></i> Grades
                </button>
            </div>
        `;
        studentsList.appendChild(studentItem);
    });
}

// Add student to class
async function addStudentToClass(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const studentData = {
        name: formData.get('student_name'),
        email: formData.get('student_email'),
        student_id: formData.get('student_id')
    };
    
    try {
        const response = await fetch(`/classes/${currentClassId}/students`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(studentData)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            alert('Student added successfully!');
            form.reset();
            // Reload students
            manageStudents(currentClassId);
            loadClasses(); // Update class stats
        } else {
            alert(result.error || 'Failed to add student');
        }
    } catch (error) {
        console.error('Error adding student:', error);
        alert('Error adding student. Please try again.');
    }
}
window.addStudentToClass = addStudentToClass;

// Delete student
async function deleteStudent(studentId) {
    if (!confirm('Are you sure you want to remove this student? This will also delete all their grades.')) {
        return;
    }
    
    try {
        const response = await fetch(`/students/${studentId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            alert('Student removed successfully!');
            // Reload students
            manageStudents(currentClassId);
            loadClasses(); // Update class stats
        } else {
            alert(result.error || 'Failed to remove student');
        }
    } catch (error) {
        console.error('Error removing student:', error);
        alert('Error removing student. Please try again.');
    }
}

// Submit batch assignment
function submitBatchAssignment(classId) {
    currentClassId = classId;
    showBatchAssignmentModal();
}
window.submitBatchAssignment = submitBatchAssignment;

// Show batch assignment modal
function showBatchAssignmentModal() {
    const modal = document.getElementById('batch-assignment-modal');
    if (modal) {
        modal.style.display = 'flex';
        // Clear form
        const form = modal.querySelector('form');
        if (form) form.reset();
        
        // Load students count
        loadStudentsForBatch();
        
        // Initialize tab functionality
        initializeBatchModalTabs();
        
        // Initialize file uploads
        initializeBatchFileUploads();
    }
}
window.showBatchAssignmentModal = showBatchAssignmentModal;

// Hide batch assignment modal
function hideBatchAssignmentModal() {
    const modal = document.getElementById('batch-assignment-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}
window.hideBatchAssignmentModal = hideBatchAssignmentModal;

// Initialize batch modal tabs
function initializeBatchModalTabs() {
    // Rubric tabs
    const rubricTabs = document.querySelectorAll('.rubric-tabs .tab');
    rubricTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabType = tab.dataset.tab;
            
            // Update tabs
            rubricTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update content
            document.querySelectorAll('#rubric-text-content, #rubric-file-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabType + '-content').classList.add('active');
        });
    });
    
    // Submission method tabs
    const submissionTabs = document.querySelectorAll('.submission-method-tabs .tab');
    submissionTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabType = tab.dataset.tab;
            
            // Update tabs
            submissionTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update content
            document.querySelectorAll('#manual-entry-content, #file-upload-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabType + '-content').classList.add('active');
        });
    });
    
    // File upload handlers
    initializeBatchFileUploads();
}

// Initialize file upload functionality
function initializeBatchFileUploads() {
    // Rubric file upload
    const rubricUpload = document.getElementById('batch-rubric-upload');
    if (rubricUpload) {
        rubricUpload.addEventListener('change', handleRubricFileUpload);
    }
    
    // Student files upload
    const studentUpload = document.getElementById('batch-student-upload');
    if (studentUpload) {
        studentUpload.addEventListener('change', handleStudentFilesUpload);
    }
    
    // Add drag and drop functionality for batch student upload
    const uploadLabel = document.querySelector('label[for="batch-student-upload"]');
    if (uploadLabel) {
        uploadLabel.addEventListener('dragover', handleDragOver);
        uploadLabel.addEventListener('dragleave', handleDragLeave);
        uploadLabel.addEventListener('drop', handleDrop);
    }

    // Initialize single file drop zone
    initializeSingleFileDropZone();
}

// Drag and drop handlers
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'var(--primary-blue)';
    e.currentTarget.style.background = 'rgba(59, 130, 246, 0.1)';
}

// Add drag and drop for single file upload
function initializeSingleFileDropZone() {
    const singleFileDropZone = document.getElementById('single-file-drop-zone');
    const fileUpload = document.getElementById('file-upload');
    
    if (!singleFileDropZone || !fileUpload) return;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        singleFileDropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        singleFileDropZone.addEventListener(eventName, () => highlight(singleFileDropZone), false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        singleFileDropZone.addEventListener(eventName, () => unhighlight(singleFileDropZone), false);
    });
    
    // Handle dropped files
    singleFileDropZone.addEventListener('drop', handleSingleFileDrop, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(element) {
    element.classList.add('drag-over');
}

function unhighlight(element) {
    element.classList.remove('drag-over');
}

function handleSingleFileDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        const file = files[0];
        const allowedTypes = ['.pdf', '.txt', '.doc', '.docx', '.jpg', '.jpeg', '.png'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (allowedTypes.includes(fileExtension)) {
            const fileUpload = document.getElementById('file-upload');
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileUpload.files = dataTransfer.files;
            
            // Trigger the change event to update UI
            const event = new Event('change', { bubbles: true });
            fileUpload.dispatchEvent(event);
            
            // Update preview
            updateSingleFilePreview(file);
        } else {
            alert('Please upload a valid assignment file (PDF, TXT, DOC, DOCX, JPG, PNG)');
        }
    }
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#d1d5db';
    e.currentTarget.style.background = '#f9fafb';
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#d1d5db';
    e.currentTarget.style.background = '#f9fafb';
    
    const files = e.dataTransfer.files;
    const fileInput = document.getElementById('batch-student-upload');
    if (fileInput && files.length > 0) {
        fileInput.files = files;
        handleStudentFilesUpload({ target: fileInput });
    }
}

// Handle rubric file upload
function handleRubricFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        const preview = document.getElementById('batch-rubric-file-preview');
        const fileName = document.getElementById('batch-rubric-file-name');
        
        if (preview && fileName) {
            fileName.textContent = file.name;
            preview.style.display = 'block';
        }
    }
}

// Handle student files upload with student mapping
function handleStudentFilesUpload(event) {
    const files = Array.from(event.target.files);
    const assignmentsContainer = document.getElementById('student-file-assignments');
    
    if (assignmentsContainer && files.length > 0) {
        // Load students for mapping
        loadStudentsForFileMapping(files);
    } else if (files.length === 0) {
        // Clear the container if no files
        if (assignmentsContainer) {
            assignmentsContainer.innerHTML = '';
        }
    }
}

// Load students for file mapping
async function loadStudentsForFileMapping(files) {
    try {
        const response = await fetch(`/classes/${currentClassId}/students`);
        if (response.ok) {
            const data = await response.json();
            const students = data.success ? data.students : data; // Handle different response formats
            const assignmentsContainer = document.getElementById('student-file-assignments');
            
            if (!assignmentsContainer) {
                console.error('student-file-assignments container not found');
                return;
            }
            
            assignmentsContainer.innerHTML = '';
            
            files.forEach((file, index) => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-assignment-item';
                fileItem.innerHTML = `
                    <div class="file-assignment-info">
                        <i class="fas fa-file"></i>
                        <span class="file-assignment-name">${file.name}</span>
                        <span class="file-size">(${formatFileSize(file.size)})</span>
                    </div>
                    <select class="student-assignment-select" data-file-index="${index}">
                        <option value="">Select Student</option>
                        ${students.map(student => `<option value="${student.id}">${student.name}</option>`).join('')}
                    </select>
                    <button type="button" class="remove-assignment" onclick="removeFileAssignment(${index})">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                assignmentsContainer.appendChild(fileItem);
            });
        }
    } catch (error) {
        console.error('Error loading students for file mapping:', error);
    }
}

// Remove file assignment
function removeFileAssignment(index) {
    const fileInput = document.getElementById('batch-student-upload');
    if (fileInput) {
        const dt = new DataTransfer();
        const files = Array.from(fileInput.files);
        
        files.forEach((file, i) => {
            if (i !== index) {
                dt.items.add(file);
            }
        });
        
        fileInput.files = dt.files;
        handleStudentFilesUpload({ target: fileInput });
    }
}
window.removeFileAssignment = removeFileAssignment;

// Remove student file
function removeStudentFile(index) {
    const fileInput = document.getElementById('batch-student-upload');
    if (fileInput) {
        const dt = new DataTransfer();
        const files = Array.from(fileInput.files);
        
        files.forEach((file, i) => {
            if (i !== index) {
                dt.items.add(file);
            }
        });
        
        fileInput.files = dt.files;
        handleStudentFilesUpload({ target: fileInput });
    }
}
window.removeStudentFile = removeStudentFile;

// Duplicate function removed - using the async version above

// Display student file mapping interface
function displayStudentFileMapping(files, students) {
    const mappingContainer = document.getElementById('student-file-mapping');
    mappingContainer.innerHTML = '';
    
    files.forEach((file, index) => {
        const mappingItem = document.createElement('div');
        mappingItem.className = 'file-mapping-item';
        mappingItem.innerHTML = `
            <div class="file-info">
                <span class="file-name">${file.name}</span>
                <span class="file-size">(${formatFileSize(file.size)})</span>
            </div>
            <div class="student-assignment">
                <label>Assign to student:</label>
                <select class="student-assignment-select" data-file-index="${index}">
                    <option value="">Select a student...</option>
                    ${students.map(student => 
                        `<option value="${student.id}">${student.name}</option>`
                    ).join('')}
                </select>
                <button type="button" class="remove-file-btn" onclick="removeFileAssignment(${index})">
                    Remove
                </button>
            </div>
        `;
        mappingContainer.appendChild(mappingItem);
    });
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Load students for batch assignment
async function loadStudentsForBatch() {
    try {
        const response = await fetch(`/classes/${currentClassId}/students`);
        if (response.ok) {
            const students = await response.json();
            const submissionsContainer = document.getElementById('batch-submissions');
            if (submissionsContainer) {
                submissionsContainer.innerHTML = '';
                
                if (students.length === 0) {
                    submissionsContainer.innerHTML = '<p>No students in this class. Please add students first.</p>';
                    return;
                }
                
                students.forEach((student, index) => {
                    const submissionDiv = document.createElement('div');
                    submissionDiv.className = 'submission-item';
                    submissionDiv.innerHTML = `
                        <label for="submission_${index}">${student.name} (${student.email})</label>
                        <textarea 
                            id="submission_${index}" 
                            name="submission_${index}" 
                            placeholder="Enter ${student.name}'s submission here..."
                            required
                        ></textarea>
                    `;
                    submissionsContainer.appendChild(submissionDiv);
                });
            }
        }
    } catch (error) {
        console.error('Error loading students for batch:', error);
    }
}

// Handle batch assignment submission
async function handleBatchAssignment(event) {
    event.preventDefault();
    alert('handleBatchAssignment function called!');
    console.log('handleBatchAssignment called');
    
    const form = event.target;
    console.log('Form element:', form);
    const formData = new FormData();
    
    // Debug: Check if form elements exist using both form and document selectors
    const assignmentNameInput = form.querySelector('[name="assignment_name"]') || document.getElementById('batch-assignment-name');
    const assignmentTypeInput = form.querySelector('[name="assignment_type"]') || document.getElementById('batch-assignment-type');
    console.log('Assignment name input:', assignmentNameInput);
    console.log('Assignment type input:', assignmentTypeInput);
    
    // Get assignment details
    let assignmentName, assignmentType;
    try {
        assignmentName = assignmentNameInput ? assignmentNameInput.value.trim() : '';
        assignmentType = assignmentTypeInput ? assignmentTypeInput.value.trim() : '';
        console.log('Assignment details:', { assignmentName, assignmentType });
        console.log('Assignment name length:', assignmentName.length);
        console.log('Assignment type length:', assignmentType.length);
    } catch (error) {
        console.error('Error getting assignment details:', error);
        alert('Error accessing form fields: ' + error.message);
        return;
    }
    
    // Check if required fields are filled
    if (!assignmentName || !assignmentType) {
        alert('Please fill in assignment name and type');
        return;
    }
    
    formData.append('assignment_name', assignmentName);
    formData.append('assignment_type', assignmentType);
    
    console.log('About to handle rubric...');
    // Handle rubric - check if file or text
    const rubricFileInput = document.getElementById('batch-rubric-upload');
    const rubricTextarea = document.getElementById('batch-rubric-text');
    const activeRubricTab = document.querySelector('.rubric-tabs .tab.active');
    console.log('Rubric elements found:', {
        rubricFileInput: !!rubricFileInput,
        rubricTextarea: !!rubricTextarea,
        activeRubricTab: !!activeRubricTab
    });
    console.log('Active rubric tab:', activeRubricTab ? activeRubricTab.dataset.tab : 'none');
    
    let hasRubric = false;
    if (activeRubricTab && activeRubricTab.dataset.tab === 'rubric-file' && rubricFileInput.files[0]) {
        formData.append('rubric_file', rubricFileInput.files[0]);
        hasRubric = true;
        console.log('Using rubric file:', rubricFileInput.files[0].name);
    } else if (rubricTextarea && rubricTextarea.value.trim()) {
        formData.append('rubric_content', rubricTextarea.value);
        hasRubric = true;
        console.log('Using rubric text, length:', rubricTextarea.value.length);
    }
    
    if (!hasRubric) {
        alert('Please provide a rubric (either upload a file or enter text)');
        return;
    }
    
    console.log('About to handle submissions...');
    // Handle submissions - check if manual entry or file upload
    const activeSubmissionTab = document.querySelector('.submission-method-tabs .tab.active');
    console.log('Submission tab element found:', !!activeSubmissionTab);
    console.log('Active submission tab:', activeSubmissionTab ? activeSubmissionTab.dataset.tab : 'none');
    
    if (activeSubmissionTab && activeSubmissionTab.dataset.tab === 'file-upload') {
        // File upload mode with student mapping
        const studentFiles = document.getElementById('batch-student-upload').files;
        console.log('Student files found:', studentFiles.length);
        const fileAssignments = [];
        
        // Get student assignments for each file
        const assignmentSelects = document.querySelectorAll('.student-assignment-select');
        console.log('Assignment selects found:', assignmentSelects.length);
        
        assignmentSelects.forEach((select, index) => {
            const studentId = select.value;
            const fileIndex = parseInt(select.dataset.fileIndex);
            console.log(`Select ${index}: studentId=${studentId}, fileIndex=${fileIndex}`);
            if (studentId && studentFiles[fileIndex]) {
                fileAssignments.push({
                    studentId: studentId,
                    fileIndex: fileIndex
                });
            }
        });
        
        console.log('File assignments:', fileAssignments);
        
        if (fileAssignments.length > 0) {
            // Send files with student mapping
            fileAssignments.forEach(assignment => {
                formData.append('student_files', studentFiles[assignment.fileIndex]);
                formData.append('student_ids', assignment.studentId);
            });
        } else {
            alert('Please assign files to students before submitting.');
            return;
        }
    } else {
        // Manual entry mode
        const submissionInputs = form.querySelectorAll('textarea[name^="submission_"]');
        const submissions = [];
        submissionInputs.forEach(input => {
            if (input.value.trim()) {
                submissions.push(input.value);
            }
        });
        formData.append('submissions', JSON.stringify(submissions));
    }
    
    console.log('About to make API request...');
    console.log('FormData contents:');
    for (let [key, value] of formData.entries()) {
        console.log(key, value);
    }
    
    try {
        // Show loading indicator
        const submitBtn = form.querySelector('button[type="submit"]');
        console.log('Submit button found:', !!submitBtn);
        const originalText = submitBtn ? submitBtn.textContent : 'Grade All Submissions';
        if (submitBtn) {
            submitBtn.textContent = 'Grading...';
            submitBtn.disabled = true;
        }
        
        const response = await fetch(`/classes/${currentClassId}/batch-assignment`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            alert('Batch assignment graded successfully!');
            hideBatchAssignmentModal();
            loadClasses(); // Update class stats
            
            // Show results
            displayBatchGradingResults(result.results);
        } else {
            alert(result.error || 'Failed to grade batch assignment');
        }
    } catch (error) {
        console.error('Error submitting batch assignment:', error);
        alert('Error submitting batch assignment. Please try again.');
    } finally {
        // Reset button
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    }
}
window.handleBatchAssignment = handleBatchAssignment;
console.log('handleBatchAssignment function attached to window:', typeof window.handleBatchAssignment);

// Test function to verify it works
window.testBatchFunction = function() {
    alert('Test function works! handleBatchAssignment type: ' + typeof window.handleBatchAssignment);
};
console.log('Test function created. Try calling window.testBatchFunction() in console');

// Student Detail Modal Functions
function showStudentDetailModal(studentId) {
    const modal = document.getElementById('student-detail-modal');
    if (modal) {
        modal.style.display = 'flex';
        loadStudentDetails(studentId);
    }
}
window.showStudentDetailModal = showStudentDetailModal;

function hideStudentDetailModal() {
    const modal = document.getElementById('student-detail-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}
window.hideStudentDetailModal = hideStudentDetailModal;

// Assignment Detail Modal Functions
function showAssignmentDetailModal(assignmentId) {
    const modal = document.getElementById('assignment-detail-modal');
    if (modal) {
        modal.style.display = 'flex';
        loadAssignmentDetails(assignmentId);
    }
}
window.showAssignmentDetailModal = showAssignmentDetailModal;

function hideAssignmentDetailModal() {
    const modal = document.getElementById('assignment-detail-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}
window.hideAssignmentDetailModal = hideAssignmentDetailModal;

// Load student details
async function loadStudentDetails(studentId) {
    try {
        // Load student info
        const studentResponse = await fetch(`/students/${studentId}`);
        if (studentResponse.ok) {
            const student = await studentResponse.json();
            
            document.getElementById('student-detail-title').textContent = `${student.name} - Details`;
            
            const basicInfo = document.getElementById('student-basic-info');
            basicInfo.innerHTML = `
                <div class="info-item">
                    <span class="info-label">Name:</span>
                    <span class="info-value">${student.name}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Email:</span>
                    <span class="info-value">${student.email}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Student ID:</span>
                    <span class="info-value">${student.student_id}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Class:</span>
                    <span class="info-value">${student.class_name || 'N/A'}</span>
                </div>
            `;
        }
        
        // Load student grades
        const gradesResponse = await fetch(`/students/${studentId}/grades`);
        if (gradesResponse.ok) {
            const grades = await gradesResponse.json();
            
            const assignmentsList = document.getElementById('student-assignments-list');
            if (grades.length === 0) {
                assignmentsList.innerHTML = '<p>No assignments found for this student.</p>';
            } else {
                assignmentsList.innerHTML = grades.map(grade => `
                    <div class="assignment-item" onclick="showAssignmentDetailModal('${grade.assignment_id}')">
                        <div class="assignment-details">
                            <div class="assignment-name">${grade.assignment_name || 'Assignment'}</div>
                            <div class="assignment-type">${grade.assignment_type || 'N/A'}</div>
                            <div class="assignment-date">${new Date(grade.graded_at).toLocaleDateString()}</div>
                        </div>
                        <div class="assignment-grade">
                            <div class="grade-score">${grade.score}%</div>
                            <div class="grade-feedback">${grade.feedback}</div>
                        </div>
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error loading student details:', error);
    }
}

// Load assignment details
async function loadAssignmentDetails(assignmentId) {
    try {
        // Load assignment info
        const assignmentResponse = await fetch(`/assignments/${assignmentId}`);
        if (assignmentResponse.ok) {
            const assignment = await assignmentResponse.json();
            
            document.getElementById('assignment-detail-title').textContent = `${assignment.name} - Details`;
            
            const basicInfo = document.getElementById('assignment-basic-info');
            basicInfo.innerHTML = `
                <div class="info-item">
                    <span class="info-label">Assignment Name:</span>
                    <span class="info-value">${assignment.name}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Type:</span>
                    <span class="info-value">${assignment.type}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Created:</span>
                    <span class="info-value">${new Date(assignment.created_at).toLocaleDateString()}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Total Submissions:</span>
                    <span class="info-value">${assignment.total_submissions}</span>
                </div>
            `;
        }
        
        // Load assignment submissions
        const submissionsResponse = await fetch(`/assignments/${assignmentId}/submissions`);
        if (submissionsResponse.ok) {
            const submissions = await submissionsResponse.json();
            
            const submissionsList = document.getElementById('assignment-submissions-list');
            if (submissions.length === 0) {
                submissionsList.innerHTML = '<p>No submissions found for this assignment.</p>';
            } else {
                submissionsList.innerHTML = submissions.map(submission => `
                    <div class="submission-item" onclick="showStudentDetailModal('${submission.student_id}')">
                        <div class="submission-details">
                            <div class="student-name">${submission.student_name}</div>
                            <div class="submission-date">${new Date(submission.graded_at).toLocaleDateString()}</div>
                        </div>
                        <div class="submission-grade">
                            <div class="submission-score">${submission.score}%</div>
                            <div class="submission-feedback">${submission.feedback}</div>
                        </div>
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error loading assignment details:', error);
    }
}

// Display batch grading results
function displayBatchGradingResults(results) {
    const modal = document.getElementById('batch-results-modal');
    if (modal) {
        // Display summary statistics
        displayBatchSummary(results);
        
        // Populate student filter
        populateBatchFilters(results);
        
        // Display results
        const resultsList = document.getElementById('batch-results-list');
        if (resultsList) {
            resultsList.innerHTML = '';
            
            results.forEach((result, index) => {
                // Handle both fraction (e.g., "7/10") and percentage (e.g., "85") formats
                const scoreText = result.score.toString();
                let displayScore, numericScore;
                
                if (scoreText.includes('/')) {
                    // Fraction format (e.g., "7/10")
                    displayScore = scoreText;
                    const [earned, total] = scoreText.split('/').map(Number);
                    numericScore = total > 0 ? (earned / total) * 100 : 0;
                } else {
                    // Percentage format (e.g., "85")
                    numericScore = parseFloat(scoreText) || 0;
                    displayScore = `${numericScore}%`;
                }
                
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item';
                resultItem.dataset.studentName = result.student_name.toLowerCase();
                resultItem.dataset.score = numericScore;
                resultItem.dataset.feedback = result.feedback.toLowerCase();
                resultItem.innerHTML = `
                    <div class="result-header">
                        <h4>${result.student_name}</h4>
                        <span class="result-score">${displayScore}</span>
                    </div>
                    <div class="result-feedback">
                        <p><strong>Feedback:</strong></p>
                        <p>${result.feedback}</p>
                    </div>
                    <div class="result-actions">
                        <button class="btn btn-sm btn-secondary" onclick="copyResultToClipboard(${index})">Copy</button>
                        <button class="btn btn-sm btn-primary" onclick="viewDetailedResult(${index})">Details</button>
                    </div>
                `;
                resultsList.appendChild(resultItem);
            });
        }
        
        // Store results globally for filtering and export
        window.currentBatchResults = results;
        
        modal.style.display = 'flex';
    }
}

// Display batch summary statistics
function displayBatchSummary(results) {
    const summaryContainer = document.getElementById('batch-results-summary');
    if (summaryContainer && results.length > 0) {
        // Convert all scores to percentage for summary calculations
        const scores = results.map(r => {
            const scoreText = r.score.toString();
            if (scoreText.includes('/')) {
                const [earned, total] = scoreText.split('/').map(Number);
                return total > 0 ? (earned / total) * 100 : 0;
            } else {
                return parseFloat(scoreText) || 0;
            }
        });
        const totalStudents = results.length;
        const averageScore = (scores.reduce((a, b) => a + b, 0) / totalStudents).toFixed(1);
        const highestScore = Math.max(...scores);
        const lowestScore = Math.min(...scores);
        const passedStudents = scores.filter(s => s >= 70).length;
        
        summaryContainer.innerHTML = `
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">Grading Summary</h4>
            <div class="batch-summary-stats">
                <div class="batch-stat-item">
                    <span class="batch-stat-value">${totalStudents}</span>
                    <span class="batch-stat-label">Total Students</span>
                </div>
                <div class="batch-stat-item">
                    <span class="batch-stat-value">${averageScore}%</span>
                    <span class="batch-stat-label">Average Score</span>
                </div>
                <div class="batch-stat-item">
                    <span class="batch-stat-value">${highestScore}%</span>
                    <span class="batch-stat-label">Highest Score</span>
                </div>
                <div class="batch-stat-item">
                    <span class="batch-stat-value">${lowestScore}%</span>
                    <span class="batch-stat-label">Lowest Score</span>
                </div>
                <div class="batch-stat-item">
                    <span class="batch-stat-value">${passedStudents}</span>
                    <span class="batch-stat-label">Passed (≥70%)</span>
                </div>
            </div>
        `;
    }
}

// Populate batch filter dropdowns
function populateBatchFilters(results) {
    const studentFilter = document.getElementById('batch-student-filter');
    
    if (studentFilter) {
        const students = [...new Set(results.map(r => r.student_name))].sort();
        studentFilter.innerHTML = '<option value="">All Students</option>';
        students.forEach(student => {
            studentFilter.innerHTML += `<option value="${student}">${student}</option>`;
        });
    }
}

// Filter batch results
function filterBatchResults() {
    const studentFilter = document.getElementById('batch-student-filter').value.toLowerCase();
    const scoreFilter = document.getElementById('batch-score-filter').value;
    const searchFilter = document.getElementById('batch-search-filter').value.toLowerCase();
    const resultItems = document.querySelectorAll('.result-item');
    
    resultItems.forEach(item => {
        const studentName = item.dataset.studentName;
        const score = parseFloat(item.dataset.score);
        const feedback = item.dataset.feedback;
        
        let studentMatch = !studentFilter || studentName.includes(studentFilter);
        let scoreMatch = true;
        let searchMatch = !searchFilter || feedback.includes(searchFilter) || studentName.includes(searchFilter);
        
        if (scoreFilter) {
            const [min, max] = scoreFilter.split('-').map(Number);
            scoreMatch = score >= min && score <= max;
        }
        
        if (studentMatch && scoreMatch && searchMatch) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// Export batch results
function exportBatchResults() {
    if (!window.currentBatchResults) {
        alert('No results to export');
        return;
    }
    
    const results = window.currentBatchResults;
    const csvContent = 'Student Name,Score,Feedback\n' + 
        results.map(r => {
            const scoreText = r.score.toString();
            const displayScore = scoreText.includes('/') ? scoreText : `${scoreText}%`;
            return `"${r.student_name}","${displayScore}","${r.feedback.replace(/"/g, '""')}"`;
        }).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batch_grading_results_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Copy result to clipboard
function copyResultToClipboard(index) {
    if (!window.currentBatchResults || !window.currentBatchResults[index]) {
        return;
    }
    
    const result = window.currentBatchResults[index];
    const scoreText = result.score.toString();
    const displayScore = scoreText.includes('/') ? scoreText : `${scoreText}%`;
    const text = `Student: ${result.student_name}\nScore: ${displayScore}\nFeedback: ${result.feedback}`;
    
    navigator.clipboard.writeText(text).then(() => {
        // Show temporary success message
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        btn.style.background = '#10b981';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy to clipboard:', err);
    });
}

// View detailed result (placeholder for future enhancement)
function viewDetailedResult(index) {
    if (!window.currentBatchResults || !window.currentBatchResults[index]) {
        return;
    }
    
    const result = window.currentBatchResults[index];
    const scoreText = result.score.toString();
    const displayScore = scoreText.includes('/') ? scoreText : `${scoreText}%`;
    alert(`Detailed view for ${result.student_name}\n\nScore: ${displayScore}\n\nFeedback:\n${result.feedback}`);
}

// Hide batch results modal
function hideBatchResultsModal() {
    const modal = document.getElementById('batch-results-modal');
    if (modal) {
        modal.style.display = 'none';
        // Clear stored results
        window.currentBatchResults = null;
    }
}
window.hideBatchResultsModal = hideBatchResultsModal;
window.filterBatchResults = filterBatchResults;
window.exportBatchResults = exportBatchResults;
window.copyResultToClipboard = copyResultToClipboard;
window.viewDetailedResult = viewDetailedResult;

// View class grades
async function viewClassGrades(classId) {
    try {
        const response = await fetch(`/classes/${classId}/grades`);
        if (response.ok) {
            const grades = await response.json();
            displayClassGrades(grades);
        } else {
            alert('Failed to load class grades');
        }
    } catch (error) {
        console.error('Error loading class grades:', error);
        alert('Error loading class grades');
    }
}
window.viewClassGrades = viewClassGrades;

// Display class grades
async function displayClassGrades(grades) {
    const modal = document.getElementById('class-grades-modal');
    if (modal) {
        // Fetch students and assignments data
        let students = [];
        let assignments = [];
        
        try {
            const studentsResponse = await fetch('/classes/students.json');
            if (studentsResponse.ok) {
                students = await studentsResponse.json();
            }
        } catch (err) {
            console.warn('Could not fetch students:', err);
        }
        
        try {
            const assignmentsResponse = await fetch('/classes/assignments.json');
            if (assignmentsResponse.ok) {
                assignments = await assignmentsResponse.json();
            }
        } catch (err) {
            console.warn('Could not fetch assignments:', err);
        }
        
        // Populate filter dropdowns
        await populateGradeFilters(grades, students, assignments);
        
        const gradesList = document.getElementById('class-grades-list');
        if (gradesList) {
            gradesList.innerHTML = '';
            
            if (grades.length === 0) {
                gradesList.innerHTML = '<p>No grades available for this class.</p>';
            } else {
                grades.forEach(grade => {
                    const gradeItem = document.createElement('div');
                    gradeItem.className = 'grade-item';
                    gradeItem.dataset.studentId = grade.student_id;
                    gradeItem.dataset.assignmentId = grade.assignment_id;
                    
                    // Look up student and assignment names
                    const student = students.find(s => s.id === grade.student_id);
                    const assignment = assignments.find(a => a.id === grade.assignment_id);
                    const studentName = student ? student.name : 'Unknown Student';
                    const assignmentName = assignment ? assignment.name : 'Unknown Assignment';
                    
                    gradeItem.innerHTML = `
                        <div class="grade-header">
                            <div class="grade-header-top">
                                <h4>${studentName}</h4>
                                <span class="score">Score: ${grade.score}</span>
                            </div>
                            <div class="grade-header-actions">
                                <button class="btn btn-sm" onclick="viewStudentDetails('${grade.student_id}')">View Student</button>
                                <button class="btn btn-sm" onclick="viewAssignmentDetails('${grade.assignment_id}')">View Assignment</button>
                            </div>
                        </div>
                        <div class="grade-details">
                            <p><strong>Assignment:</strong> ${assignmentName}</p>
                            <p><strong>Graded:</strong> ${new Date(grade.graded_at).toLocaleDateString()}</p>
                            <p><strong>Feedback:</strong></p>
                            <p>${grade.feedback}</p>
                        </div>
                    `;
                    gradesList.appendChild(gradeItem);
                });
            }
        }
        modal.style.display = 'flex';
    }
}

// Populate grade filter dropdowns
async function populateGradeFilters(grades, students = [], assignments = []) {
    const studentFilter = document.getElementById('student-filter');
    const assignmentFilter = document.getElementById('assignment-filter');
    
    if (studentFilter) {
        const uniqueStudentIds = [...new Set(grades.map(g => g.student_id))];
        const gradeStudents = uniqueStudentIds.map(id => {
            const student = students.find(s => s.id === id);
            return { id, name: student ? student.name : 'Unknown Student' };
        });
        studentFilter.innerHTML = '<option value="">All Students</option>';
        gradeStudents.forEach(student => {
            studentFilter.innerHTML += `<option value="${student.id}">${student.name}</option>`;
        });
    }
    
    if (assignmentFilter) {
        const uniqueAssignmentIds = [...new Set(grades.map(g => g.assignment_id))];
        const gradeAssignments = uniqueAssignmentIds.map(id => {
            const assignment = assignments.find(a => a.id === id);
            return { id, name: assignment ? assignment.name : 'Unknown Assignment' };
        });
        assignmentFilter.innerHTML = '<option value="">All Assignments</option>';
        gradeAssignments.forEach(assignment => {
            assignmentFilter.innerHTML += `<option value="${assignment.id}">${assignment.name}</option>`;
        });
    }
}

// Hide class grades modal
function hideClassGradesModal() {
    const modal = document.getElementById('class-grades-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Filter grades by student, assignment, score, or search term
function filterGrades() {
    const studentFilter = document.getElementById('student-filter').value;
    const assignmentFilter = document.getElementById('assignment-filter').value;
    const scoreFilter = document.getElementById('grade-score-filter').value;
    const searchFilter = document.getElementById('grade-search-filter').value.toLowerCase();
    const gradeItems = document.querySelectorAll('.grade-item');
    
    gradeItems.forEach(item => {
        const studentId = item.dataset.studentId;
        const assignmentId = item.dataset.assignmentId;
        const scoreText = item.querySelector('.score').textContent;
        let score = 0;
        
        // Extract score from "Score: X/Y" format and convert to percentage
        const scoreRegexMatch = scoreText.match(/Score:\s*(\d+)\/(\d+)/);
        if (scoreRegexMatch) {
            const earned = parseFloat(scoreRegexMatch[1]);
            const total = parseFloat(scoreRegexMatch[2]);
            score = total > 0 ? Math.round((earned / total) * 100) : 0;
        }
        const feedback = item.querySelector('.grade-details').textContent.toLowerCase();
        const studentName = item.querySelector('h4').textContent.toLowerCase();
        
        const studentMatch = !studentFilter || studentId === studentFilter;
        const assignmentMatch = !assignmentFilter || assignmentId === assignmentFilter;
        
        let scoreMatch = true;
        if (scoreFilter) {
            const [min, max] = scoreFilter.split('-').map(Number);
            scoreMatch = score >= min && score <= max;
        }
        
        const searchMatch = !searchFilter || 
            feedback.includes(searchFilter) || 
            studentName.includes(searchFilter);
        
        if (studentMatch && assignmentMatch && scoreMatch && searchMatch) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// View student details
function viewStudentDetails(studentId) {
    showStudentDetailModal(studentId);
}

// View assignment details
function viewAssignmentDetails(assignmentId) {
    showAssignmentDetailModal(assignmentId);
}

// View student grades
async function viewStudentGrades(studentId) {
    try {
        // Fetch student information first
        let studentName = 'Unknown Student';
        try {
            const studentResponse = await fetch('/classes/students.json');
            if (studentResponse.ok) {
                const students = await studentResponse.json();
                const student = students.find(s => s.id === studentId);
                if (student) {
                    studentName = student.name;
                }
            }
        } catch (err) {
            console.warn('Could not fetch student info:', err);
        }

        const response = await fetch(`/students/${studentId}/grades`);
        if (response.ok) {
            const grades = await response.json();
            // Load assignments data
            let assignments = [];
            try {
                const assignmentsResponse = await fetch('/classes/assignments.json');
                if (assignmentsResponse.ok) {
                    assignments = await assignmentsResponse.json();
                }
            } catch (err) {
                console.warn('Could not fetch assignments:', err);
            }
            displayStudentGrades(grades, assignments, studentName);
        } else {
            alert('Failed to load student grades');
        }
    } catch (error) {
        console.error('Error loading student grades:', error);
        alert('Error loading student grades');
    }
}

// Display student grades
function displayStudentGrades(grades, assignments = [], studentName = 'Student') {
    const modal = document.getElementById('student-grades-modal');
    if (modal) {
        // Update modal title with student name
        const modalTitle = modal.querySelector('.modal-header h3');
        if (modalTitle) {
            modalTitle.textContent = `${studentName} - Grades`;
        }
        
        const gradesList = document.getElementById('student-grades-list');
        if (gradesList) {
            gradesList.innerHTML = '';
            
            if (grades.length === 0) {
                gradesList.innerHTML = '<p>No grades available for this student.</p>';
            } else {
                grades.forEach(grade => {
                    const gradeItem = document.createElement('div');
                    gradeItem.className = 'grade-item';
                    
                    // Handle score display (fraction or percentage)
                    const scoreText = grade.score.toString();
                    const displayScore = scoreText.includes('/') ? scoreText : `${scoreText}/100`;
                    
                    // Look up assignment name
                    const assignment = assignments.find(a => a.id === grade.assignment_id);
                    const assignmentName = assignment ? assignment.name : 'Unknown Assignment';
                    const assignmentType = assignment ? assignment.type : 'Unknown Type';
                    
                    gradeItem.innerHTML = `
                        <div class="grade-header">
                            <span class="score">${displayScore}</span>
                            <div class="grade-date">${new Date(grade.graded_at).toLocaleDateString()}</div>
                        </div>
                        <div class="grade-details">
                            <div class="grade-assignment">
                                <strong>Assignment:</strong> ${assignmentName}
                                <div class="assignment-type">${assignmentType}</div>
                            </div>
                            <div class="grade-feedback">
                                <strong>Feedback:</strong><br>
                                ${grade.feedback}
                            </div>
                        </div>
                    `;
                    gradesList.appendChild(gradeItem);
                });
            }
        }
        modal.style.display = 'flex';
    }
}

// Hide student grades modal
function hideStudentGradesModal() {
    const modal = document.getElementById('student-grades-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}