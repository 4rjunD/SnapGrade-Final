/**
 * Rubric Upload Fix for SnapGrade
 * This script fixes issues with the rubric upload functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Fix for rubric upload functionality
    fixRubricUpload();
});

function fixRubricUpload() {
    const rubricUpload = document.getElementById('rubric-upload');
    const rubricDropZone = document.getElementById('rubric-drop-zone');
    const rubricFilePreview = document.getElementById('rubric-file-preview');
    const rubricFileName = document.getElementById('rubric-file-name');
    const removeRubricFileBtn = document.getElementById('remove-rubric-file');

    // If any of the elements don't exist, exit early
    if (!rubricUpload || !rubricDropZone) return;

    console.log("Initializing rubric upload fix...");

    // Add change event listener to rubric upload input
    rubricUpload.addEventListener('change', function(event) {
        console.log("Rubric upload change event triggered");
        const file = this.files[0];
        
        if (file) {
            console.log(`Selected file: ${file.name}`);
            
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
            
            // For TXT files, read directly
            if (fileExt === '.txt') {
                const reader = new FileReader();
                reader.onload = function(e) {
                    window.uploadedRubricContent = e.target.result;
                    if (rubricFileName) {
                        rubricFileName.textContent = file.name;
                    }
                    
                    // Update upload text
                    const uploadText = document.querySelector('#rubric-drop-zone .upload-text');
                    if (uploadText) {
                        uploadText.textContent = 'Rubric file selected';
                    }
                    
                    // Show preview of uploaded content
                    const rubricPreview = document.getElementById('rubric-preview');
                    const rubricPreviewContainer = document.getElementById('rubric-preview-container');
                    if (rubricPreview) {
                        rubricPreview.textContent = window.uploadedRubricContent.substring(0, 500) + 
                            (window.uploadedRubricContent.length > 500 ? '...' : '');
                    }
                    if (rubricPreviewContainer) {
                        rubricPreviewContainer.style.display = 'block';
                    }
                    
                    console.log("Text file processed successfully, content length: " + window.uploadedRubricContent.length);
                };
                reader.readAsText(file);
            } else {
                // For other file types, send to backend
                const reader = new FileReader();
                reader.onload = async function(e) {
                    const base64Data = e.target.result.split(',')[1]; // Remove data URL prefix
                    
                    try {
                        console.log("Sending file to backend for processing...");
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
                            window.uploadedRubricContent = data.rubric_content;
                            if (rubricFileName) {
                                rubricFileName.textContent = file.name;
                            }
                            
                            // Update upload text
                            const uploadText = document.querySelector('#rubric-drop-zone .upload-text');
                            if (uploadText) {
                                uploadText.textContent = 'Rubric file selected';
                            }
                            
                            // Show preview of uploaded content
                            const rubricPreview = document.getElementById('rubric-preview');
                            const rubricPreviewContainer = document.getElementById('rubric-preview-container');
                            if (rubricPreview) {
                                rubricPreview.textContent = window.uploadedRubricContent.substring(0, 500) + 
                                    (window.uploadedRubricContent.length > 500 ? '...' : '');
                            }
                            if (rubricPreviewContainer) {
                                rubricPreviewContainer.style.display = 'block';
                            }
                            
                            console.log("File processed successfully, content length: " + window.uploadedRubricContent.length);
                        } else {
                            throw new Error(data.error || 'Failed to process file');
                        }
                    } catch (error) {
                        console.error('Error processing rubric file:', error);
                        alert(`Error processing file: ${error.message}`);
                        window.uploadedRubricContent = null;
                        if (rubricFilePreview) {
                            rubricFilePreview.style.display = 'none';
                        }
                    }
                };
                reader.readAsDataURL(file);
            }
        }
    });

    // Add click event listener to remove button
    if (removeRubricFileBtn) {
        removeRubricFileBtn.addEventListener('click', function() {
            console.log("Remove rubric file button clicked");
            
            // Clear the file input
            if (rubricUpload) {
                rubricUpload.value = '';
            }
            
            // Reset the UI
            if (rubricFilePreview) {
                rubricFilePreview.style.display = 'none';
            }
            
            // Update upload text
            const uploadText = document.querySelector('#rubric-drop-zone .upload-text');
            if (uploadText) {
                uploadText.textContent = 'Click to upload or drag & drop rubric';
            }
            
            // Hide the preview
            const rubricPreviewContainer = document.getElementById('rubric-preview-container');
            if (rubricPreviewContainer) {
                rubricPreviewContainer.style.display = 'none';
            }
            
            // Clear uploaded content
            window.uploadedRubricContent = null;
        });
    }

    // Enhanced drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        rubricDropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        rubricDropZone.addEventListener(eventName, function() {
            rubricDropZone.classList.add('drag-over');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        rubricDropZone.addEventListener(eventName, function() {
            rubricDropZone.classList.remove('drag-over');
        }, false);
    });
    
    // Handle dropped files
    rubricDropZone.addEventListener('drop', function(e) {
        console.log("File dropped on rubric drop zone");
        
        const dt = e.dataTransfer;
        const file = dt.files[0];
        
        if (file) {
            // Set the file in the input element
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            rubricUpload.files = dataTransfer.files;
            
            // Trigger the change event
            const event = new Event('change', { bubbles: true });
            rubricUpload.dispatchEvent(event);
        }
    }, false);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
}
