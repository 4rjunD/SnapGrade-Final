from flask import Flask, request, jsonify, url_for, send_from_directory, render_template, session, redirect, send_file
from flask_cors import CORS
from flask_mail import Mail, Message
from grader import grade_assignment
from grader.engine import grade_assignment_with_vision
from image_processor import extract_text_from_image, get_file_from_dropbox
from image_processor.ocr import extract_text_from_image, detect_diagrams_in_image, extract_text_with_metadata_from_image
from file_processor import extract_text_from_file
from excel_export import create_excel_for_batch_results, save_excel_file
from config import Config
import traceback
import os
import uuid
import base64
import io
import json
from datetime import datetime

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')

# Enable CORS for all routes
CORS(app)

# Configure session
app.secret_key = 'your-secret-key-change-this-in-production'

# Valid teacher IDs
VALID_TEACHER_IDS = {
    'TEACHER001': {'name': 'Ms. Johnson', 'subject': 'English'},
    'TEACHER002': {'name': 'Mr. Smith', 'subject': 'Mathematics'},
    'TEACHER003': {'name': 'Dr. Williams', 'subject': 'Science'},
    'TEACHER004': {'name': 'Ms. Davis', 'subject': 'History'},
    'TEACHER005': {'name': 'Mr. Brown', 'subject': 'Art'}
}

# Authentication middleware
def require_auth():
    if 'teacher_id' not in session or session['teacher_id'] not in VALID_TEACHER_IDS:
        return jsonify({'error': 'Authentication required'}), 401
    return None

# Configure Flask-Mail
app.config['MAIL_SERVER'] = Config.MAIL_SERVER
app.config['MAIL_PORT'] = Config.MAIL_PORT
app.config['MAIL_USE_TLS'] = Config.MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = Config.MAIL_USE_SSL
app.config['MAIL_USERNAME'] = Config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = Config.MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = Config.MAIL_DEFAULT_SENDER

# Initialize Flask-Mail
mail = Mail(app)

# Configure upload folder
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# Create upload folder if it doesn't exist
# This line is already Python 3 compatible
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create rubrics folder if it doesn't exist
RUBRICS_FOLDER = os.path.join(os.path.dirname(__file__), 'rubrics')
os.makedirs(RUBRICS_FOLDER, exist_ok=True)
RUBRICS_FILE = os.path.join(RUBRICS_FOLDER, 'rubrics.json')

# Initialize rubrics file if it doesn't exist
if not os.path.exists(RUBRICS_FILE):
    with open(RUBRICS_FILE, 'w') as f:
        json.dump([], f)

# Create classes folder and files if they don't exist
CLASSES_FOLDER = os.path.join(os.path.dirname(__file__), 'classes')
os.makedirs(CLASSES_FOLDER, exist_ok=True)
CLASSES_FILE = os.path.join(CLASSES_FOLDER, 'classes.json')
STUDENTS_FILE = os.path.join(CLASSES_FOLDER, 'students.json')
ASSIGNMENTS_FILE = os.path.join(CLASSES_FOLDER, 'assignments.json')
GRADES_FILE = os.path.join(CLASSES_FOLDER, 'grades.json')

# Initialize class management files if they don't exist
for file_path in [CLASSES_FILE, STUDENTS_FILE, ASSIGNMENTS_FILE, GRADES_FILE]:
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump([], f)

@app.route('/grade', methods=['POST'])
def grade():
    """
    Endpoint to grade assignments based on provided rubrics.
    
    Expected JSON input:
    {
        "assignment_type": "Essay",
        "submission": "Student's answer text here",
        "rubric": "Detailed grading rubric here"
    }
    
    Returns:
    {
        "score": 95,
        "feedback": "Excellent structure and clarity. Minor grammar errors."
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['assignment_type', 'submission', 'rubric']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": "Missing required field: {}".format(field)
                }), 400
        
        # Extract data
        assignment_type = data['assignment_type']
        submission = data['submission']
        rubric = data['rubric']
        
        # Grade the assignment
        result = grade_assignment(assignment_type, submission, rubric)
        
        # Return the grading result
        return jsonify(result), 200
        
    except Exception as e:
        # Log the error
        print(f"Error processing request: {str(e)}")
        print(traceback.format_exc())
        
        # Return error response
        return jsonify({
            "error": "An error occurred while processing the request",
            "details": str(e)
        }), 500

@app.route('/grade-image', methods=['POST'])
def grade_image():
    """
    Enhanced endpoint that prioritizes MCQ and diagram detection/grading
    before falling back to standard OCR processing.
    
    Expected JSON input:
    {
        "assignment_type": "Essay",
        "image_file": "base64_encoded_image_data",
        "rubric": "Detailed grading rubric here"
    }
    
    Returns:
    {
        "score": 95,
        "feedback": "Excellent structure and clarity. Minor grammar errors.",
        "extracted_text": "The text extracted from the image",
        "processing_method": "Standard OCR + Gemini or GPT-4 Vision (Diagram Detection)"
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['assignment_type', 'image_file', 'rubric']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": "Missing required field: {}".format(field)
                }), 400
        
        # Extract data
        assignment_type = data['assignment_type']
        image_data = data['image_file']
        rubric = data['rubric']
        
        # Validate image data
        if not image_data:
            return jsonify({
                "error": "Empty image data provided",
                "details": "The image_file field contains no data"
            }), 400
        
        # Decode base64 image data
        try:
            # Handle potential padding issues in base64
            padding = 4 - (len(image_data) % 4) if len(image_data) % 4 else 0
            image_data = image_data + ('=' * padding)
            
            try:
                image_bytes = base64.b64decode(image_data)
                print(f"Successfully decoded image data, size: {len(image_bytes)} bytes")
                
                if len(image_bytes) < 100:  # Arbitrary small size check
                    return jsonify({
                        "error": "Invalid image data",
                        "details": "The decoded image is too small to be valid"
                    }), 400
                    
            except Exception as decode_error:
                print(f"Base64 decoding error: {str(decode_error)}")
                return jsonify({
                    "error": "Invalid base64 image data",
                    "details": str(decode_error)
                }), 400
                
        except Exception as e:
            return jsonify({
                "error": "Error processing image data",
                "details": str(e)
            }), 400
        
        # Extract text, student name, and assignment title using enhanced methods
        print("Starting enhanced metadata extraction with corner text analysis...")
        extraction_result = extract_text_with_metadata_from_image(image_bytes, assignment_type)
        extracted_text = extraction_result['extracted_text']
        student_name_info = extraction_result['student_name_info']
        student_name = student_name_info.get('student_name') if student_name_info else None
        assignment_title_info = extraction_result.get('assignment_title_info', {})
        assignment_title = assignment_title_info.get('assignment_title')
        corner_text = extraction_result.get('corner_text', {})
        
        print(f"Extracted student name: {student_name}")
        print(f"Extracted assignment title: {assignment_title}")
        
        # Enhanced debug logging for student name extraction
        print(f"Student name info: {json.dumps(student_name_info)}")
        print(f"Assignment title info: {json.dumps(assignment_title_info)}")
        print(f"Corner text analysis: {json.dumps(corner_text)}")
        print(f"Processing notes: {extraction_result.get('processing_notes', 'No processing notes')}")
        
        # Grade the assignment with student name and assignment title
        if hasattr(Config, 'GRADING_ENGINE') and Config.GRADING_ENGINE == 'gemini':
            from grader.gemini_engine import grade_assignment_with_gemini
            result = grade_assignment_with_gemini(assignment_type, extracted_text, rubric, student_name, assignment_title)
        else:
            result = grade_assignment(assignment_type, extracted_text, rubric, student_name)
        
        # Add extracted text and metadata to the result
        result['extracted_text'] = extracted_text
        result['student_name_info'] = student_name_info
        result['assignment_title_info'] = assignment_title_info
        result['corner_text'] = corner_text
        result['processing_notes'] = extraction_result.get('processing_notes', 'No processing notes')
        result['processing_method'] = 'Enhanced OCR + Corner Text Analysis + Gemini with Metadata Extraction'
        
        # Make sure student name is directly accessible in the result
        if student_name:
            result['student_name'] = student_name
        
        # Make sure assignment title is directly accessible in the result
        if assignment_title:
            result['assignment_title'] = assignment_title
        
        # Return the grading result
        return jsonify(result), 200
        
    except Exception as e:
        # Log the error
        print(f"Error processing image: {str(e)}")
        print(traceback.format_exc())
        
        # Return error response
        return jsonify({
            "error": "An error occurred while processing the image",
            "details": str(e)
        }), 500

@app.route('/grade-image-legacy', methods=['POST'])
def grade_image_legacy():
    """
    Legacy endpoint that uses the original diagram detection + routing approach.
    Maintained for backward compatibility.
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['assignment_type', 'image_file', 'rubric']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": "Missing required field: {}".format(field)
                }), 400
        
        # Extract data
        assignment_type = data['assignment_type']
        image_data = data['image_file']
        rubric = data['rubric']
        
        # Validate image data
        if not image_data:
            return jsonify({
                "error": "Empty image data provided",
                "details": "The image_file field contains no data"
            }), 400
        
        # Decode base64 image data
        try:
            # Handle potential padding issues in base64
            padding = 4 - (len(image_data) % 4) if len(image_data) % 4 else 0
            image_data = image_data + ('=' * padding)
            
            try:
                image_bytes = base64.b64decode(image_data)
                print(f"Successfully decoded image data, size: {len(image_bytes)} bytes")
                
                if len(image_bytes) < 100:  # Arbitrary small size check
                    return jsonify({
                        "error": "Invalid image data",
                        "details": "The decoded image is too small to be valid"
                    }), 400
                    
            except Exception as decode_error:
                print(f"Base64 decoding error: {str(decode_error)}")
                return jsonify({
                    "error": "Invalid base64 image data",
                    "details": str(decode_error)
                }), 400
                
        except Exception as e:
            return jsonify({
                "error": "Error processing image data",
                "details": str(e)
            }), 400
        
        # Step 1: Detect if image contains diagrams (original approach)
        print("Detecting diagrams in image...")
        diagram_info = detect_diagrams_in_image(image_bytes)
        print(f"Diagram detection result: {diagram_info}")
        
        # Step 2: Route to appropriate grading method (original logic)
        if diagram_info.get('has_diagrams', False) and diagram_info.get('confidence') in ['high', 'medium']:
            print("Routing to GPT-4 Vision for diagram analysis...")
            try:
                result = grade_assignment_with_vision(assignment_type, image_bytes, rubric, diagram_info)
                result['processing_method'] = 'GPT-4 Vision (Legacy Diagram Detection)'
                result['diagram_info'] = diagram_info
            except Exception as vision_error:
                print(f"GPT-4 Vision grading failed: {str(vision_error)}")
                print("Falling back to standard OCR + text grading...")
                # Fallback to standard process
                extracted_text = extract_text_from_image(image_bytes, assignment_type)
                result = grade_assignment(assignment_type, extracted_text, rubric)
                result['processing_method'] = 'Standard OCR + Gemini (Vision Fallback)'
                result['extracted_text'] = extracted_text
        else:
            print("Using standard OCR + text grading process...")
            # Enhanced process: OCR with student name extraction
            ocr_result = extract_text_with_metadata_from_image(image_bytes, assignment_type)
            extracted_text = ocr_result['extracted_text']
            student_name_info = ocr_result['student_name_info']
            
            result = grade_assignment(assignment_type, extracted_text, rubric)
            result['processing_method'] = 'Standard OCR + Gemini with Name Extraction (Legacy)'
            result['extracted_text'] = extracted_text
            result['student_name_info'] = student_name_info
            result['diagram_info'] = diagram_info
        
        # Return the grading result
        return jsonify(result), 200
        
    except Exception as e:
        # Log the error
        print(f"Error processing image: {str(e)}")
        print(traceback.format_exc())
        
        # Return error response
        return jsonify({
            "error": "An error occurred while processing the image",
            "details": str(e)
        }), 500

@app.route('/grade-dropbox-alt', methods=['POST'])
def grade_dropbox_alt():
    """
    Endpoint to grade assignments from Dropbox images.
    
    Expected JSON input:
    {
        "assignment_type": "Essay",
        "dropbox_path": "/path/to/image/in/dropbox.jpg",
        "rubric": "Detailed grading rubric here"
    }
    
    OR
    
    {
        "assignment_type": "Essay",
        "dropbox_shared_link": "https://www.dropbox.com/s/...",
        "rubric": "Detailed grading rubric here"
    }
    
    Returns:
    {
        "score": 95,
        "feedback": "Excellent structure and clarity. Minor grammar errors.",
        "extracted_text": "The text extracted from the image"
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        if 'assignment_type' not in data or 'rubric' not in data:
            return jsonify({
                "error": "Missing required fields: assignment_type or rubric"
            }), 400
            
        if 'dropbox_path' not in data and 'dropbox_shared_link' not in data:
            return jsonify({
                "error": "Missing required field: dropbox_path or dropbox_shared_link"
            }), 400
        
        # Extract data
        assignment_type = data['assignment_type']
        rubric = data['rubric']
        
        # Get the file from Dropbox
        if 'dropbox_path' in data:
            from image_processor.dropbox_handler import get_file_from_dropbox
            image_bytes = get_file_from_dropbox(data['dropbox_path'])
        else:
            from image_processor.dropbox_handler import get_file_from_shared_link
            image_bytes = get_file_from_shared_link(data['dropbox_shared_link'])
        
        # Process the image to extract text
        extracted_text = extract_text_from_image(image_bytes)
        
        # Grade the assignment using the extracted text
        result = grade_assignment(assignment_type, extracted_text, rubric)
        
        # Add the extracted text to the result
        result['extracted_text'] = extracted_text
        
        # Return the grading result
        return jsonify(result), 200
        
    except Exception as e:
        # Log the error
        print(f"Error processing Dropbox file: {str(e)}")
        print(traceback.format_exc())
        
        # Return error response
        return jsonify({
            "error": "An error occurred while processing the Dropbox file",
            "details": str(e)
        }), 500

@app.route('/upload-file', methods=['POST'])
def upload_file():
    """
    Endpoint to upload a file to the server.
    
    Expected form data:
    - file: The file to upload
    
    Returns:
    {
        "success": true,
        "file_id": "unique_file_id",
        "filename": "uploaded_filename.jpg"
    }
    """
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({
                "error": "No file part in the request"
            }), 400
            
        file = request.files['file']
        
        # If user does not select file, browser also
        # submits an empty part without filename
        if file.filename == '':
            return jsonify({
                "error": "No file selected"
            }), 400
            
        # Generate a unique filename to prevent collisions
        file_id = str(uuid.uuid4())
        filename = file_id + '_' + file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        file.save(file_path)
        
        return jsonify({
            "success": True,
            "file_id": file_id,
            "filename": filename
        }), 200
        
    except Exception as e:
        # Log the error
        print("Error uploading file: {}".format(str(e)))
        print(traceback.format_exc())
        
        # Return error response
        return jsonify({
            "error": "An error occurred while uploading the file",
            "details": str(e)
        }), 500

@app.route('/grade-uploaded-file', methods=['POST'])
def grade_uploaded_file():
    """
    Endpoint to grade assignments from previously uploaded files.
    
    Expected JSON input:
    {
        "assignment_type": "Essay",
        "filename": "uploaded_filename.jpg",
        "rubric": "Detailed grading rubric here"
    }
    
    Returns:
    {
        "score": 95,
        "feedback": "Excellent structure and clarity. Minor grammar errors.",
        "extracted_text": "The text extracted from the image"
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['assignment_type', 'filename', 'rubric']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": "Missing required field: {}".format(field)
                }), 400
        
        # Extract data
        assignment_type = data['assignment_type']
        filename = data['filename']
        rubric = data['rubric']
        
        # Construct the file path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Check if the file exists
        if not os.path.exists(file_path):
            return jsonify({
                "error": "File not found: {}".format(filename)
            }), 404
        
        # Read the file
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        # Determine file type and extract text accordingly
        file_ext = os.path.splitext(filename.lower())[1]
        
        if file_ext == '.pdf':
            # Process PDF file
            extracted_text = extract_text_from_file(file_bytes, filename)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
            # Process image file
            extracted_text = extract_text_from_image(file_bytes)
        elif file_ext in ['.txt', '.doc', '.docx']:
            # Process document file
            extracted_text = extract_text_from_file(file_bytes, filename)
        else:
            return jsonify({
                "error": "Unsupported file type: {}".format(file_ext),
                "details": "Supported file types: PDF, images (JPG, PNG, etc.), TXT, DOC, DOCX"
            }), 400
        
        # Check for processing errors
        if extracted_text.startswith('[') and 'ERROR' in extracted_text:
            return jsonify({
                "error": "File processing failed",
                "details": extracted_text
            }), 500
        
        # Grade the assignment using the extracted text
        result = grade_assignment(assignment_type, extracted_text, rubric)
        
        # Add the extracted text to the result
        result['extracted_text'] = extracted_text
        
        # Return the grading result
        return jsonify(result), 200
        
    except Exception as e:
        # Log the error
        print("Error processing uploaded file: {}".format(str(e)))
        print(traceback.format_exc())
        
        # Return error response
        return jsonify({
            "error": "An error occurred while processing the uploaded file",
            "details": str(e)
        }), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    Endpoint to serve uploaded files.
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/grade-dropbox', methods=['POST'])
def grade_dropbox():
    """
    Endpoint to grade assignments from Dropbox images.
    
    Expected JSON input:
    {
        "assignment_type": "Essay",
        "dropbox_path": "/path/to/image/in/dropbox.jpg",
        "rubric": "Detailed grading rubric here"
    }
    
    OR
    
    {
        "assignment_type": "Essay",
        "dropbox_shared_link": "https://www.dropbox.com/s/...",
        "rubric": "Detailed grading rubric here"
    }
    
    Returns:
    {
        "score": 95,
        "feedback": "Excellent structure and clarity. Minor grammar errors.",
        "extracted_text": "The text extracted from the image"
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        if 'assignment_type' not in data or 'rubric' not in data:
            return jsonify({
                "error": "Missing required fields: assignment_type or rubric"
            }), 400
            
        if 'dropbox_path' not in data and 'dropbox_shared_link' not in data:
            return jsonify({
                "error": "Missing required field: dropbox_path or dropbox_shared_link"
            }), 400
        
        # Extract data
        assignment_type = data['assignment_type']
        rubric = data['rubric']
        
        # Get the file from Dropbox
        if 'dropbox_path' in data:
            from image_processor.dropbox_handler import get_file_from_dropbox
            image_bytes = get_file_from_dropbox(data['dropbox_path'])
        else:
            from image_processor.dropbox_handler import get_file_from_shared_link
            image_bytes = get_file_from_shared_link(data['dropbox_shared_link'])
        
        # Process the image to extract text
        extracted_text = extract_text_from_image(image_bytes)
        
        # Grade the assignment using the extracted text
        result = grade_assignment(assignment_type, extracted_text, rubric)
        
        # Add the extracted text to the result
        result['extracted_text'] = extracted_text
        
        # Return the grading result
        return jsonify(result), 200
        
    except Exception as e:
        # Log the error
        print(f"Error processing Dropbox file: {str(e)}")
        print(traceback.format_exc())
        
        # Return error response
        return jsonify({
            "error": "An error occurred while processing the Dropbox file",
            "details": str(e)
        }), 500

# Add this after your other imports
import os

# Add this after the upload folder creation
# Create assignment folder if it doesn't exist
os.makedirs(Config.ASSIGNMENT_FOLDER, exist_ok=True)

# Add this new route to your app.py file
@app.route('/grade-assignment', methods=['POST'])
def grade_assignment_file():
    """
    Endpoint to grade assignments from files in the assignment folder.
    
    Expected JSON input:
    {
        "assignment_type": "Essay",
        "filename": "assignment1.jpg",
        "rubric": "Detailed grading rubric here"
    }
    
    Returns:
    {
        "score": 95,
        "feedback": "Excellent structure and clarity. Minor grammar errors.",
        "extracted_text": "The text extracted from the image"
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['assignment_type', 'filename', 'rubric']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": "Missing required field: {}".format(field)
                }), 400
        
        # Extract data
        assignment_type = data['assignment_type']
        filename = data['filename']
        rubric = data['rubric']
        
        # Construct the file path
        file_path = os.path.join(Config.ASSIGNMENT_FOLDER, filename)
        
        # Check if the file exists
        if not os.path.exists(file_path):
            return jsonify({
                "error": "File not found: {}".format(filename)
            }), 404
        
        # Read the file
        with open(file_path, 'rb') as f:
            image_bytes = f.read()
        
        # Process the image to extract text
        extracted_text = extract_text_from_image(image_bytes)
        
        # Grade the assignment using the extracted text
        result = grade_assignment(assignment_type, extracted_text, rubric)
        
        # Add the extracted text to the result
        result['extracted_text'] = extracted_text
        
        # Return the grading result
        return jsonify(result), 200
        
    except Exception as e:
        # Log the error
        print("Error processing assignment file: {}".format(str(e)))
        print(traceback.format_exc())
        
        # Return error response
        return jsonify({
            "error": "An error occurred while processing the assignment file",
            "details": str(e)
        }), 500

@app.route('/assignments/<filename>')
def assignment_file(filename):
    """
    Endpoint to serve assignment files.
    """
    return send_from_directory(Config.ASSIGNMENT_FOLDER, filename)

@app.route('/process-rubric', methods=['POST'])
def process_rubric():
    """
    Endpoint to process uploaded rubric files and extract text content.
    
    Expected JSON input:
    {
        "file_data": "base64_encoded_file_data",
        "filename": "rubric.pdf"
    }
    
    Returns:
    {
        "rubric_content": "Extracted text content from the file"
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['file_data', 'filename']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": "Missing required field: {}".format(field)
                }), 400
        
        # Extract data
        file_data = data['file_data']
        filename = data['filename']
        
        # Validate file data
        if not file_data:
            return jsonify({
                "error": "Empty file data provided",
                "details": "The file_data field contains no data"
            }), 400
        
        # Decode base64 file data
        try:
            # Handle potential padding issues in base64
            padding = 4 - (len(file_data) % 4) if len(file_data) % 4 else 0
            file_data = file_data + ('=' * padding)
            
            file_bytes = base64.b64decode(file_data)
            print(f"Successfully decoded file data, size: {len(file_bytes)} bytes")
            
            if len(file_bytes) < 10:  # Arbitrary small size check
                return jsonify({
                    "error": "Invalid file data",
                    "details": "The decoded file is too small to be valid"
                }), 400
                
        except Exception as decode_error:
            print(f"Base64 decoding error: {str(decode_error)}")
            return jsonify({
                "error": "Invalid base64 file data",
                "details": str(decode_error)
            }), 400
        
        # Extract text from the file
        try:
            print(f"Extracting text from file: {filename}")
            rubric_content = extract_text_from_file(file_bytes, filename)
            print(f"Text extraction complete. Extracted {len(rubric_content)} characters")
            
            # Check for processing errors
            if rubric_content.startswith("[FILE PROCESSING ERROR:"):
                return jsonify({
                    "error": "File processing failed",
                    "details": rubric_content
                }), 500
            
            if not rubric_content.strip():
                return jsonify({
                    "error": "No content found in file",
                    "details": "The file appears to be empty or contains no extractable text"
                }), 400
                
        except Exception as processing_error:
            print(f"File processing error: {str(processing_error)}")
            print(traceback.format_exc())
            return jsonify({
                "error": "File processing failed",
                "details": str(processing_error)
            }), 500
        
        # Return the extracted rubric content
        return jsonify({
            "rubric_content": rubric_content
        }), 200
        
    except Exception as e:
        # Log the error
        print(f"Error processing rubric file: {str(e)}")
        print(traceback.format_exc())
        
        # Return error response
        return jsonify({
            "error": "An error occurred while processing the rubric file",
            "details": str(e)
        }), 500

@app.route('/grade-pdf-direct', methods=['POST'])
def grade_pdf_direct():
    """
    Endpoint to grade PDF submissions directly using GPT-4 Vision without text extraction.
    
    Expected JSON input:
    {
        "assignment_type": "Essay",
        "file_data": "base64_encoded_pdf_data",
        "filename": "submission.pdf",
        "rubric": "Detailed grading rubric here"
    }
    
    Returns:
    {
        "score": "8/10",
        "feedback": "Detailed feedback here"
    }
    """
    try:
        from file_processor.document_processor import extract_text_from_file
        from openai import OpenAI
        import base64
        import json
        import traceback
        import os
        import tempfile
        from pdf2image import convert_from_bytes
        
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['assignment_type', 'file_data', 'filename', 'rubric']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": "Missing required field: {}".format(field)
                }), 400
        
        # Extract data
        assignment_type = data['assignment_type']
        file_data = data['file_data']
        filename = data['filename']
        rubric = data['rubric']
        
        # Validate file data
        if not file_data:
            return jsonify({
                "error": "Empty file data provided"
            }), 400
        
        # Decode base64 file data
        try:
            padding = 4 - (len(file_data) % 4) if len(file_data) % 4 else 0
            file_data = file_data + ('=' * padding)
            file_bytes = base64.b64decode(file_data)
            print(f"Successfully decoded PDF file data, size: {len(file_bytes)} bytes")
        except Exception as decode_error:
            return jsonify({
                "error": "Invalid base64 file data",
                "details": str(decode_error)
            }), 400
        
        # FORCE GPT-4 Vision processing - skip text extraction entirely
        try:
            print("Converting PDF to images for GPT-4 Vision (FORCED MODE)...")
            images = convert_from_bytes(file_bytes, dpi=300, fmt='PNG')  # Higher DPI
            
            if not images or len(images) == 0:
                return jsonify({
                    "error": "PDF conversion failed",
                    "details": "Could not convert PDF to images for GPT-4 Vision processing. Please ensure the PDF contains readable content."
                }), 500
            
            print(f"Successfully converted PDF to {len(images)} image(s) for GPT-4 Vision")
            
            # Process with GPT-4 Vision directly
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            
            # Prepare images for GPT-4 Vision
            image_contents = []
            for i, img in enumerate(images):
                # Convert PIL image to base64
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                base64_image = base64.b64encode(img_bytes).decode('utf-8')
                
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                })
            
            # Create comprehensive grading prompt
            vision_prompt = f"""Grade this {assignment_type} assignment using GPT-4 Vision with maximum accuracy.

ASSIGNMENT TYPE: {assignment_type}

RUBRIC:
{rubric}

**GRADING INSTRUCTIONS:**
1. Analyze ALL pages of this assignment thoroughly
2. Extract and evaluate all student work, answers, and responses
3. For multiple choice: Award full credit if correct answer is selected
4. For mathematical work: Focus on final answers and recognizable methods
5. For written responses: Evaluate content quality and completeness
6. Be generous with partial credit for unclear handwriting
7. Provide detailed feedback for each question/section

**CRITICAL: This is a PDF that failed traditional OCR processing. Use your vision capabilities to directly analyze the content without relying on text extraction.**

Respond in JSON format:
{{
    "score": "earned_points/total_points",
    "feedback": "Detailed grading feedback with question-by-question analysis",
    "processing_method": "GPT-4 Vision Direct (PDF)",
    "pages_processed": {len(images)}
}}"""
            
            # Prepare messages with text and all images
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": vision_prompt
                        }
                    ] + image_contents
                }
            ]
            
            # Call GPT-4 Vision
            response = client.chat.completions.create(
                model=Config.OPENAI_VISION_MODEL,
                messages=messages,
                max_tokens=4000,
                temperature=0.1
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Clean JSON if needed
            if content.startswith('```json'):
                content = content[7:-3].strip()
            elif content.startswith('```'):
                content = content[3:-3].strip()
            
            result = json.loads(content)
            
            print(f"GPT-4 Vision grading completed successfully for {len(images)} pages")
            return jsonify(result), 200
            
        except Exception as e:
            print(f"GPT-4 Vision PDF processing error: {str(e)}")
            print(traceback.format_exc())
            return jsonify({
                "error": "GPT-4 Vision processing failed",
                "details": f"Could not process PDF with GPT-4 Vision: {str(e)}"
            }), 500
            
    except ImportError as e:
        if "pdf2image" in str(e):
            return jsonify({
                "error": "pdf2image library not available",
                "details": "PDF processing requires pdf2image library"
            }), 500
        else:
            return jsonify({
                "error": "Missing dependency",
                "details": str(e)
            }), 500
    
    except Exception as e:
        print(f"Error in direct PDF grading: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "error": "An error occurred while grading the PDF",
            "details": str(e)
        }), 500

@app.route('/grade-pdf-vision-only', methods=['POST'])
def grade_pdf_vision_only():
    """
    Endpoint to grade PDF submissions using ONLY GPT-4 Vision, bypassing all text extraction.
    Use this when traditional OCR fails.
    
    Expected JSON input:
    {
        "assignment_type": "Essay",
        "file_data": "base64_encoded_pdf_data",
        "filename": "submission.pdf",
        "rubric": "Detailed grading rubric here"
    }
    
    Returns:
    {
        "score": "8/10",
        "feedback": "Detailed feedback here",
        "individual_pages": [page results]
    }
    """
    try:
        from file_processor.document_processor import extract_text_from_file
        from openai import OpenAI
        import base64
        import json
        import traceback
        import os
        import tempfile
        from pdf2image import convert_from_bytes
        
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['assignment_type', 'file_data', 'filename', 'rubric']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": "Missing required field: {}".format(field)
                }), 400
        
        # Extract data
        assignment_type = data['assignment_type']
        file_data = data['file_data']
        filename = data['filename']
        rubric = data['rubric']
        
        # Validate file data
        if not file_data:
            return jsonify({
                "error": "Empty file data provided"
            }), 400
        
        # Decode base64 file data
        try:
            padding = 4 - (len(file_data) % 4) if len(file_data) % 4 else 0
            file_data = file_data + ('=' * padding)
            file_bytes = base64.b64decode(file_data)
            print(f"Successfully decoded PDF file data, size: {len(file_bytes)} bytes")
        except Exception as decode_error:
            return jsonify({
                "error": "Invalid base64 file data",
                "details": str(decode_error)
            }), 400
        
        # FORCE Vision-only processing
        print("VISION-ONLY MODE: Converting PDF to images...")
        images = convert_from_bytes(file_bytes, dpi=300, fmt='PNG')
        
        if not images or len(images) == 0:
            return jsonify({
                "error": "PDF conversion failed",
                "details": "Could not convert PDF to images. Please try uploading as individual image files."
            }), 500
            
        print(f"Successfully converted PDF to {len(images)} image(s) for Vision-only processing")
        
        # Use the enhanced vision grading from analyze_and_grade_mcq_diagrams_first
        from image_processor.ocr import analyze_and_grade_mcq_diagrams_first
        
        # Process each page and combine results
        all_results = []
        for i, img in enumerate(images):
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            page_result = analyze_and_grade_mcq_diagrams_first(img_bytes, assignment_type, rubric)
            page_result['page_number'] = i + 1
            all_results.append(page_result)
        
        # Combine results from all pages
        combined_result = {
            "score": "Combined from all pages",
            "feedback": "\n\n".join([f"**Page {r['page_number']}:**\n{r.get('feedback', '')}" for r in all_results]),
            "processing_method": "GPT-4 Vision Only (Multi-page PDF)",
            "pages_processed": len(images),
            "individual_pages": all_results
        }
        
        return jsonify(combined_result), 200
        
    except ImportError as e:
        if "pdf2image" in str(e):
            return jsonify({
                "error": "pdf2image library not available",
                "details": "PDF processing requires pdf2image library"
            }), 500
        else:
            return jsonify({
                "error": "Missing dependency",
                "details": str(e)
            }), 500
    
    except Exception as e:
        print(f"Vision-only PDF processing error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "error": "Vision-only processing failed",
            "details": str(e)
        }), 500

@app.route('/grade-and-store', methods=['POST'])
def grade_and_store_assignment():
    """
    Grade an assignment and store it with student name if detected.
    
    Expected JSON input:
    {
        "assignment_type": "Essay",
        "image_file": "base64_encoded_image_data",
        "rubric": "Detailed grading rubric here",
        "class_id": "optional_class_id",
        "assignment_id": "optional_assignment_id"
    }
    """
    try:
        data = request.get_json()
        
        # First grade the assignment (reuse existing logic)
        grade_result = grade_image()
        
        if grade_result[1] != 200:  # If grading failed
            return grade_result
            
        grade_data = grade_result[0].get_json()
        
        # If student name was detected, try to match with existing students
        if grade_data.get('student_name_info', {}).get('student_name'):
            student_name = grade_data['student_name_info']['student_name']
            
            # Load existing students
            with open(STUDENTS_FILE, 'r') as f:
                students = json.load(f)
            
            # Try to find matching student
            matching_student = None
            for student in students:
                if student_name.lower() in student['name'].lower() or student['name'].lower() in student_name.lower():
                    matching_student = student
                    break
            
            if matching_student:
                # Store the grade with student association
                grade_entry = {
                    "id": str(uuid.uuid4()),
                    "student_id": matching_student['id'],
                    "student_name": matching_student['name'],
                    "detected_name": student_name,
                    "assignment_type": data.get('assignment_type'),
                    "score": grade_data.get('score'),
                    "feedback": grade_data.get('feedback'),
                    "extracted_text": grade_data.get('extracted_text'),
                    "processing_method": grade_data.get('processing_method'),
                    "timestamp": datetime.now().isoformat(),
                    "class_id": data.get('class_id'),
                    "assignment_id": data.get('assignment_id')
                }
                
                # Load and update grades
                with open(GRADES_FILE, 'r') as f:
                    grades = json.load(f)
                
                grades.append(grade_entry)
                
                with open(GRADES_FILE, 'w') as f:
                    json.dump(grades, f, indent=2)
                
                grade_data['stored_grade'] = True
                grade_data['matched_student'] = matching_student['name']
            else:
                grade_data['stored_grade'] = False
                grade_data['reason'] = 'No matching student found in database'
        else:
            grade_data['stored_grade'] = False
            grade_data['reason'] = 'No student name detected in assignment'
        
        return jsonify(grade_data), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error processing and storing assignment",
            "details": str(e)
        }), 500
    try:
        from file_processor.document_processor import extract_text_from_file
        from openai import OpenAI
        import base64
        import json
        import traceback
        import os
        import tempfile
        from pdf2image import convert_from_bytes
        
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['assignment_type', 'file_data', 'filename', 'rubric']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": "Missing required field: {}".format(field)
                }), 400
        
        # Extract data
        assignment_type = data['assignment_type']
        file_data = data['file_data']
        filename = data['filename']
        rubric = data['rubric']
        
        # Validate file data
        if not file_data:
            return jsonify({
                "error": "Empty file data provided"
            }), 400
        
        # Decode base64 file data
        try:
            padding = 4 - (len(file_data) % 4) if len(file_data) % 4 else 0
            file_data = file_data + ('=' * padding)
            file_bytes = base64.b64decode(file_data)
            print(f"Successfully decoded PDF file data, size: {len(file_bytes)} bytes")
        except Exception as decode_error:
            return jsonify({
                "error": "Invalid base64 file data",
                "details": str(decode_error)
            }), 400
        
        # Try image-based processing first, fall back to text if needed
        images = None
        extracted_text = None
        use_vision = False
        
        # First attempt: Convert PDF to images for GPT-4 Vision
        try:
            print("Converting PDF to images for GPT-4 Vision...")
            images = convert_from_bytes(file_bytes, dpi=200, fmt='PNG')
            
            if images and len(images) > 0:
                print(f"Successfully converted PDF to {len(images)} image(s)")
                use_vision = True
            else:
                print("PDF conversion produced no images, falling back to text extraction")
        except Exception as image_error:
            print(f"PDF to image conversion failed: {str(image_error)}")
            print("Falling back to text extraction...")
        
        # Fallback: Extract text if image conversion failed
        if not use_vision:
            try:
                print("Extracting text from PDF for grading...")
                
                # Save PDF bytes to temporary file for processing
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(file_bytes)
                    temp_file_path = temp_file.name
                
                # Extract text using existing document processor
                extracted_text = extract_text_from_file(temp_file_path)
                
                # Clean up temporary file
                os.unlink(temp_file_path)
                
                if not extracted_text or len(extracted_text.strip()) < 10:
                    return jsonify({
                        "error": "Could not process PDF",
                        "details": "PDF could not be converted to images or text. Please try uploading as an image file."
                    }), 500
                
                print(f"Successfully extracted {len(extracted_text)} characters from PDF")
            except Exception as extraction_error:
                print(f"PDF text extraction error: {str(extraction_error)}")
                print(traceback.format_exc())
                return jsonify({
                    "error": "PDF processing failed",
                    "details": str(extraction_error)
                }), 500
        
        # Initialize OpenAI client
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Prepare content for GPT-4 based on processing method
        if use_vision:
            # Prepare images for GPT-4 Vision
            image_contents = []
            for i, img in enumerate(images):
                # Convert PIL image to base64
                import io
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_base64}"
                    }
                })
            
            # Create grading prompt for vision
            grading_prompt = f"""
You are an expert grader. Please grade this {assignment_type} submission based on the provided rubric.

RUBRIC:
{rubric}

INSTRUCTIONS:
1. Carefully examine all pages of the submission images
2. Analyze the rubric to determine the total possible points
3. Grade the submission according to the rubric criteria
4. If the rubric specifies a total other than 100 points, output the score as a fraction (e.g., "7/10")
5. If the rubric uses a 0-100 scale or doesn't specify, output a numeric score (0-100)
6. Provide detailed feedback explaining your grading decisions

Please respond in JSON format:
{{
    "score": "your_score_here",
    "feedback": "detailed feedback explaining the grade"
}}
"""
            
            # Prepare message content for vision
            message_content = [{"type": "text", "text": grading_prompt}]
            message_content.extend(image_contents)
            
            print("Sending PDF images to GPT-4 Vision for direct grading...")
            print(f"Message content items: {len(message_content)}")
        else:
            # Create grading prompt for text
            grading_prompt = f"""
You are an expert grader. Please grade this {assignment_type} submission based on the provided rubric.

RUBRIC:
{rubric}

SUBMISSION TEXT:
{extracted_text}

INSTRUCTIONS:
1. Carefully analyze the submission text
2. Analyze the rubric to determine the total possible points
3. Grade the submission according to the rubric criteria
4. If the rubric specifies a total other than 100 points, output the score as a fraction (e.g., "7/10")
5. If the rubric uses a 0-100 scale or doesn't specify, output a numeric score (0-100)
6. Provide detailed feedback explaining your grading decisions

Please respond in JSON format:
{{
    "score": "your_score_here",
    "feedback": "detailed feedback explaining the grade"
}}
"""
            
            print("Sending PDF text to GPT-4 for direct grading...")
            print(f"Message content length: {len(grading_prompt)} characters")
        
        # Call GPT-4 for grading
        try:
            if use_vision:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": message_content
                        }
                    ],
                    max_tokens=1500,
                    temperature=0.3
                )
                print("Successfully received response from GPT-4 Vision")
            else:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "user",
                            "content": grading_prompt
                        }
                    ],
                    max_tokens=1500,
                    temperature=0.3
                )
                print("Successfully received response from GPT-4")
        except Exception as gpt_error:
            model_name = "GPT-4 Vision" if use_vision else "GPT-4"
            print(f"{model_name} API error: {str(gpt_error)}")
            print(traceback.format_exc())
            return jsonify({
                "error": f"{model_name} API failed",
                "details": str(gpt_error)
            }), 500
        
        # Extract and parse the response
        gpt_response = response.choices[0].message.content.strip()
        model_name = "GPT-4 Vision" if use_vision else "GPT-4"
        print(f"{model_name} response: {gpt_response}")
        
        # Parse JSON response
        try:
            import json
            import re
            
            # Clean up the response by removing markdown code blocks if present
            cleaned_response = gpt_response
            if cleaned_response.startswith("```json"):
                cleaned_response = re.sub(r'^```json\s*', '', cleaned_response)
                cleaned_response = re.sub(r'\s*```$', '', cleaned_response)
            elif cleaned_response.startswith("```"):
                cleaned_response = re.sub(r'^```\s*', '', cleaned_response)
                cleaned_response = re.sub(r'\s*```$', '', cleaned_response)
            
            cleaned_response = cleaned_response.strip()
            print(f"Cleaned response for parsing: {cleaned_response}")
            
            result = json.loads(cleaned_response)
            
            if 'score' not in result or 'feedback' not in result:
                raise ValueError("Missing required fields in GPT response")
            
            return jsonify({
                "score": result['score'],
                "feedback": result['feedback']
            }), 200
            
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            return jsonify({
                "error": "Failed to parse GPT response",
                "details": "GPT response was not valid JSON",
                "raw_response": gpt_response
            }), 500
        
    except ImportError as e:
        if "pdf2image" in str(e):
            return jsonify({
                "error": "pdf2image library not available",
                "details": "PDF processing requires pdf2image library"
            }), 500
        else:
            return jsonify({
                "error": "Missing dependency",
                "details": str(e)
            }), 500
    
    except Exception as e:
        print(f"Error in direct PDF grading: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "error": "An error occurred while grading the PDF",
            "details": str(e)
        }), 500

@app.route('/grade-file-upload', methods=['POST'])
def grade_file_upload():
    """
    Endpoint to grade assignments from direct file uploads with rubric.
    
    Expected form data:
    - assignment_type: The type of assignment
    - rubric: The grading rubric (text)
    - submission: Optional text submission
    - file: Optional file upload (PDF, image, or document)
    
    Returns:
    {
        "score": 95,
        "feedback": "Excellent structure and clarity.",
        "extracted_text": "The text extracted from the file"
    }
    """
    try:
        # Get form data
        assignment_type = request.form.get('assignment_type')
        rubric = request.form.get('rubric')
        submission_text = request.form.get('submission', '')
        
        # Validate required fields
        if not assignment_type:
            return jsonify({
                "error": "Missing required field: assignment_type"
            }), 400
            
        if not rubric:
            return jsonify({
                "error": "Missing required field: rubric"
            }), 400
        
        # Check if we have either text submission or file upload
        has_file = 'file' in request.files and request.files['file'].filename != ''
        has_text = submission_text.strip() != ''
        
        if not has_file and not has_text:
            return jsonify({
                "error": "Either text submission or file upload is required"
            }), 400
        
        extracted_text = ""
        
        # Process file if uploaded
        if has_file:
            file = request.files['file']
            filename = file.filename
            file_bytes = file.read()
            
            # Determine file type and extract text
            file_ext = os.path.splitext(filename.lower())[1]
            
            if file_ext == '.pdf':
                # Process PDF file
                extracted_text = extract_text_from_file(file_bytes, filename)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                # Process image file
                extracted_text = extract_text_from_image(file_bytes)
            elif file_ext in ['.txt', '.doc', '.docx']:
                # Process document file
                extracted_text = extract_text_from_file(file_bytes, filename)
            else:
                return jsonify({
                    "error": "Unsupported file type: {}".format(file_ext),
                    "details": "Supported file types: PDF, images (JPG, PNG, etc.), TXT, DOC, DOCX"
                }), 400
            
            # Check for processing errors
            if extracted_text.startswith('[') and 'ERROR' in extracted_text:
                return jsonify({
                    "error": "File processing failed",
                    "details": extracted_text
                }), 500
        
        # Use text submission if no file or combine with extracted text
        if has_text and has_file:
            final_submission = "Text Submission:\n{}\n\nExtracted from File:\n{}".format(submission_text, extracted_text)
        elif has_text:
            final_submission = submission_text
        else:
            final_submission = extracted_text
        
        # Grade the assignment
        result = grade_assignment(assignment_type, final_submission, rubric)
        
        # Add extracted text to result if file was processed
        if has_file:
            result['extracted_text'] = extracted_text
        
        return jsonify(result), 200
        
    except Exception as e:
        # Log the error
        print("Error processing file upload: {}".format(str(e)))
        print(traceback.format_exc())
        
        # Return error response
        return jsonify({
            "error": "An error occurred while processing the request",
            "details": str(e)
        }), 500

@app.route('/grade-batch-upload', methods=['POST'])
def grade_batch_upload():
    """
    Endpoint to grade multiple assignments from file uploads.
    
    Expected form data:
    - assignment_type: The type of assignment
    - rubric: The grading rubric (text)
    - files: Multiple file uploads (PDF, image, or document)
    
    Returns:
    {
        "results": [
            {
                "filename": "student1.pdf",
                "score": 95,
                "feedback": "Excellent work.",
                "extracted_text": "The text extracted from the file"
            },
            ...
        ],
        "summary": {
            "total_files": 3,
            "processed": 2,
            "failed": 1,
            "average_score": 87.5
        }
    }
    """
    try:
        # Get form data
        assignment_type = request.form.get('assignment_type')
        rubric = request.form.get('rubric')
        
        # Validate required fields
        if not assignment_type:
            return jsonify({
                "error": "Missing required field: assignment_type"
            }), 400
            
        if not rubric:
            return jsonify({
                "error": "Missing required field: rubric"
            }), 400
        
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({
                "error": "No files uploaded"
            }), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                "error": "No files selected"
            }), 400
        
        results = []
        total_files = len(files)
        processed = 0
        failed = 0
        total_score = 0
        
        for file in files:
            if file.filename == '':
                continue
                
            try:
                filename = file.filename
                file_bytes = file.read()
                
                # Determine file type and extract text
                file_ext = os.path.splitext(filename.lower())[1]
                extracted_text = ""
                
                if file_ext == '.pdf':
                    # Process PDF file
                    extracted_text = extract_text_from_file(file_bytes, filename)
                elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                    # Process image file
                    extracted_text = extract_text_from_image(file_bytes)
                elif file_ext in ['.txt', '.doc', '.docx']:
                    # Process document file
                    extracted_text = extract_text_from_file(file_bytes, filename)
                else:
                    results.append({
                        "filename": filename,
                        "error": f"Unsupported file type: {file_ext}",
                        "details": "Supported file types: PDF, images (JPG, PNG, etc.), TXT, DOC, DOCX"
                    })
                    failed += 1
                    continue
                
                # Check for processing errors
                if extracted_text.startswith('[') and 'ERROR' in extracted_text:
                    results.append({
                        "filename": filename,
                        "error": "File processing failed",
                        "details": extracted_text
                    })
                    failed += 1
                    continue
                
                # Grade the assignment
                grading_result = grade_assignment(assignment_type, extracted_text, rubric)
                
                # Add filename and extracted text to result
                score_value = grading_result.get('score', 0)
                
                # Convert score to numeric value for calculation
                numeric_score = 0
                if isinstance(score_value, str) and '/' in score_value:
                    # Handle fractional scores like "7/10"
                    try:
                        parts = score_value.split('/')
                        if len(parts) == 2:
                            earned = float(parts[0])
                            total = float(parts[1])
                            numeric_score = (earned / total) * 100  # Convert to percentage
                    except (ValueError, ZeroDivisionError):
                        numeric_score = 0
                else:
                    # Handle numeric scores
                    try:
                        numeric_score = float(score_value)
                    except (ValueError, TypeError):
                        numeric_score = 0
                
                result = {
                    "filename": filename,
                    "score": score_value,  # Keep original score format for display
                    "feedback": grading_result.get('feedback', ''),
                    "extracted_text": extracted_text
                }
                
                results.append(result)
                processed += 1
                total_score += numeric_score  # Use numeric score for calculation
                
            except Exception as file_error:
                print(f"Error processing file {file.filename}: {str(file_error)}")
                results.append({
                    "filename": file.filename,
                    "error": "File processing failed",
                    "details": str(file_error)
                })
                failed += 1
        
        # Calculate average score
        average_score = total_score / processed if processed > 0 else 0
        
        # Prepare summary
        summary = {
            "total_files": total_files,
            "processed": processed,
            "failed": failed,
            "average_score": round(average_score, 1)
        }
        
        # Generate Excel file
        assignment_name = request.form.get('assignment_name', 'Batch Upload')
        try:
            # Use our excel export module to create the file
            from excel_export import create_excel_for_batch_results, save_excel_file
            
            # Create the Excel file and get its path
            excel_path, excel_filename = create_excel_for_batch_results(results, summary, assignment_name)
            
            # Save/copy the Excel file to the exports directory if needed
            export_dir = os.path.join(app.root_path, 'exports')
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            excel_path = save_excel_file(excel_path, excel_filename, export_dir)
            
            # Include the Excel file path in the response
            excel_url = url_for('download_excel_export', filename=excel_filename, _external=True)
            
            return jsonify({
                "results": results,
                "summary": summary,
                "excel_export": {
                    "filename": excel_filename,
                    "url": excel_url
                }
            }), 200
        except Exception as excel_error:
            print(f"Error generating Excel file: {str(excel_error)}")
            import traceback as tb
            print(tb.format_exc())
            # Return results without Excel if there's an error
            return jsonify({
                "results": results,
                "summary": summary,
                "excel_export_error": str(excel_error)
            }), 200
        
    except Exception as e:
        # Log the error
        print(f"Error processing batch upload: {str(e)}")
        print(traceback.format_exc())
        
        # Return error response
        return jsonify({
            "error": "An error occurred while processing the batch upload",
            "details": str(e)
        }), 500

@app.route('/contact', methods=['POST'])
def contact():
    """
    Endpoint to handle contact form submissions and send emails.
    
    Expected JSON input:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "subject": "technical-support",
        "message": "I need help with..."
    }
    
    Returns:
    {
        "success": true,
        "message": "Email sent successfully"
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Create email message
        subject_map = {
            'technical-support': 'Technical Support Request',
            'billing': 'Billing & Subscription Inquiry',
            'feature-request': 'Feature Request',
            'bug-report': 'Bug Report',
            'general-inquiry': 'General Inquiry',
            'other': 'Other Inquiry'
        }
        
        email_subject = f"SnapGrade Contact: {subject_map.get(data['subject'], 'Contact Form')}"
        
        # Create message
        msg = Message(
            subject=email_subject,
            recipients=[Config.CONTACT_EMAIL],
            reply_to=data['email']
        )
        
        # Email body
        msg.body = f"""
New contact form submission from SnapGrade:

Name: {data['name']}
Email: {data['email']}
Subject: {subject_map.get(data['subject'], data['subject'])}

Message:
{data['message']}

---
This message was sent from the SnapGrade contact form.
        """
        
        # Send email
        mail.send(msg)
        
        return jsonify({
            "success": True,
            "message": "Thank you for your message! We'll get back to you soon."
        })
        
    except Exception as e:
        print(f"Error sending contact email: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Failed to send message. Please try again later.",
            "details": str(e)
        }), 500

@app.route('/rubrics', methods=['GET'])
def get_rubrics():
    """
    Get all saved rubrics.
    """
    try:
        with open(RUBRICS_FILE, 'r') as f:
            rubrics = json.load(f)
        return jsonify({"rubrics": rubrics}), 200
    except Exception as e:
        print(f"Error getting rubrics: {str(e)}")
        return jsonify({"error": "Failed to retrieve rubrics"}), 500

@app.route('/rubrics', methods=['POST'])
def create_rubric():
    """
    Create a new rubric.
    
    Expected JSON input:
    {
        "name": "Rubric Name",
        "description": "Rubric description",
        "type": "Essay",
        "content": "Detailed rubric content"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'description', 'type', 'content']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Load existing rubrics
        with open(RUBRICS_FILE, 'r') as f:
            rubrics = json.load(f)
        
        # Create new rubric
        new_rubric = {
            "id": str(uuid.uuid4()),
            "name": data['name'].strip(),
            "description": data['description'].strip(),
            "type": data['type'].strip(),
            "content": data['content'].strip(),
            "created_date": datetime.now().strftime("%b %d, %Y"),
            "created_timestamp": datetime.now().isoformat()
        }
        
        # Add to rubrics list
        rubrics.append(new_rubric)
        
        # Save back to file
        with open(RUBRICS_FILE, 'w') as f:
            json.dump(rubrics, f, indent=2)
        
        return jsonify({
            "success": True,
            "message": "Rubric created successfully",
            "rubric": new_rubric
        }), 201
        
    except Exception as e:
        print(f"Error creating rubric: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Failed to create rubric",
            "details": str(e)
        }), 500

@app.route('/rubrics/<rubric_id>', methods=['DELETE'])
def delete_rubric(rubric_id):
    """
    Delete a rubric by ID.
    """
    try:
        # Load existing rubrics
        with open(RUBRICS_FILE, 'r') as f:
            rubrics = json.load(f)
        
        # Find and remove the rubric
        rubrics = [r for r in rubrics if r['id'] != rubric_id]
        
        # Save back to file
        with open(RUBRICS_FILE, 'w') as f:
            json.dump(rubrics, f, indent=2)
        
        return jsonify({
            "success": True,
            "message": "Rubric deleted successfully"
        }), 200
        
    except Exception as e:
        print(f"Error deleting rubric: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to delete rubric"
        }), 500

# Class Management Endpoints
@app.route('/classes', methods=['GET'])
def get_classes():
    """Get all classes for the current teacher"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        with open(CLASSES_FILE, 'r') as f:
            all_classes = json.load(f)
        
        # Filter classes by current teacher
        teacher_classes = [c for c in all_classes if c.get('teacher_id') == session['teacher_id']]
        
        return jsonify(teacher_classes), 200
    except Exception as e:
        print(f"Error loading classes: {str(e)}")
        return jsonify({"error": "Failed to load classes"}), 500

@app.route('/classes', methods=['POST'])
def create_class():
    """Create a new class for the current teacher"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('name').strip():
            return jsonify({
                "success": False,
                "error": "Class name is required"
            }), 400
        
        # Load existing classes
        with open(CLASSES_FILE, 'r') as f:
            classes = json.load(f)
        
        # Create new class with teacher_id
        new_class = {
            "id": str(uuid.uuid4()),
            "name": data['name'].strip(),
            "description": data.get('description', '').strip(),
            "teacher_id": session['teacher_id'],
            "teacher_name": session['teacher_name'],
            "created_date": datetime.now().strftime("%b %d, %Y"),
            "student_count": 0
        }
        
        # Add to classes list
        classes.append(new_class)
        
        # Save back to file
        with open(CLASSES_FILE, 'w') as f:
            json.dump(classes, f, indent=2)
        
        return jsonify({
            "success": True,
            "message": "Class created successfully",
            "class": new_class
        }), 201
        
    except Exception as e:
        print(f"Error creating class: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to create class"
        }), 500

@app.route('/classes/<class_id>', methods=['DELETE'])
def delete_class(class_id):
    """Delete a class"""
    try:
        # Load existing classes
        with open(CLASSES_FILE, 'r') as f:
            classes = json.load(f)
        
        # Find and remove the class
        classes = [c for c in classes if c['id'] != class_id]
        
        # Save back to file
        with open(CLASSES_FILE, 'w') as f:
            json.dump(classes, f, indent=2)
        
        # Also remove associated students and grades
        with open(STUDENTS_FILE, 'r') as f:
            students = json.load(f)
        students = [s for s in students if s['class_id'] != class_id]
        with open(STUDENTS_FILE, 'w') as f:
            json.dump(students, f, indent=2)
        
        with open(GRADES_FILE, 'r') as f:
            grades = json.load(f)
        grades = [g for g in grades if g['class_id'] != class_id]
        with open(GRADES_FILE, 'w') as f:
            json.dump(grades, f, indent=2)
        
        return jsonify({
            "success": True,
            "message": "Class deleted successfully"
        }), 200
        
    except Exception as e:
        print(f"Error deleting class: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to delete class"
        }), 500

# Student Management Endpoints
@app.route('/classes/<class_id>/students', methods=['GET'])
def get_students(class_id):
    """Get all students in a class"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    # Verify teacher owns this class
    try:
        with open(CLASSES_FILE, 'r') as f:
            classes = json.load(f)
        
        class_obj = next((c for c in classes if c['id'] == class_id), None)
        if not class_obj or class_obj.get('teacher_id') != session['teacher_id']:
            return jsonify({"error": "Class not found or access denied"}), 403
        
        with open(STUDENTS_FILE, 'r') as f:
            students = json.load(f)
        
        class_students = [s for s in students if s['class_id'] == class_id]
        return jsonify(class_students), 200
    except Exception as e:
        print(f"Error loading students: {str(e)}")
        return jsonify({"error": "Failed to load students"}), 500

@app.route('/classes/<class_id>/students', methods=['POST'])
def add_student(class_id):
    """Add a student to a class"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Load existing students
        with open(STUDENTS_FILE, 'r') as f:
            students = json.load(f)
        
        # Create new student
        new_student = {
            "id": str(uuid.uuid4()),
            "class_id": class_id,
            "name": data['name'].strip(),
            "email": data['email'].strip(),
            "student_id": data.get('student_id', '').strip(),
            "created_at": datetime.now().isoformat()
        }
        
        # Add to students list
        students.append(new_student)
        
        # Save back to file
        with open(STUDENTS_FILE, 'w') as f:
            json.dump(students, f, indent=2)
        
        # Update class student count
        with open(CLASSES_FILE, 'r') as f:
            classes = json.load(f)
        
        for class_obj in classes:
            if class_obj['id'] == class_id:
                class_obj['student_count'] = len([s for s in students if s['class_id'] == class_id])
                break
        
        with open(CLASSES_FILE, 'w') as f:
            json.dump(classes, f, indent=2)
        
        return jsonify({
            "success": True,
            "message": "Student added successfully",
            "student": new_student
        }), 201
        
    except Exception as e:
        print(f"Error adding student: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to add student"
        }), 500

@app.route('/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student"""
    try:
        # Load existing students
        with open(STUDENTS_FILE, 'r') as f:
            students = json.load(f)
        
        # Find the student to get class_id
        student_to_delete = next((s for s in students if s['id'] == student_id), None)
        if not student_to_delete:
            return jsonify({"error": "Student not found"}), 404
        
        class_id = student_to_delete['class_id']
        
        # Remove the student
        students = [s for s in students if s['id'] != student_id]
        
        # Save back to file
        with open(STUDENTS_FILE, 'w') as f:
            json.dump(students, f, indent=2)
        
        # Update class student count
        with open(CLASSES_FILE, 'r') as f:
            classes = json.load(f)
        
        for class_obj in classes:
            if class_obj['id'] == class_id:
                class_obj['student_count'] = len([s for s in students if s['class_id'] == class_id])
                break
        
        with open(CLASSES_FILE, 'w') as f:
            json.dump(classes, f, indent=2)
        
        # Also remove associated grades
        with open(GRADES_FILE, 'r') as f:
            grades = json.load(f)
        grades = [g for g in grades if g['student_id'] != student_id]
        with open(GRADES_FILE, 'w') as f:
            json.dump(grades, f, indent=2)
        
        return jsonify({
            "success": True,
            "message": "Student deleted successfully"
        }), 200
        
    except Exception as e:
        print(f"Error deleting student: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to delete student"
        }), 500

# Assignment and Grading Endpoints
@app.route('/classes/<class_id>/assignments', methods=['POST'])
def submit_batch_assignment(class_id):
    """Submit an assignment for all students in a class"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    # Verify teacher owns this class
    try:
        with open(CLASSES_FILE, 'r') as f:
            classes = json.load(f)
        
        class_obj = next((c for c in classes if c['id'] == class_id), None)
        if not class_obj or class_obj.get('teacher_id') != session['teacher_id']:
            return jsonify({
                "success": False,
                "error": "Class not found or access denied"
            }), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['assignment_name', 'assignment_type', 'rubric_content', 'submissions']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Load students for this class
        with open(STUDENTS_FILE, 'r') as f:
            students = json.load(f)
        
        class_students = [s for s in students if s['class_id'] == class_id]
        
        if len(data['submissions']) != len(class_students):
            return jsonify({
                "success": False,
                "error": "Number of submissions must match number of students in class"
            }), 400
        
        # Create assignment record
        assignment_id = str(uuid.uuid4())
        assignment = {
            "id": assignment_id,
            "class_id": class_id,
            "name": data['assignment_name'],
            "type": data['assignment_type'],
            "rubric_content": data['rubric_content'],
            "created_at": datetime.now().isoformat(),
            "total_submissions": len(data['submissions'])
        }
        
        # Save assignment
        with open(ASSIGNMENTS_FILE, 'r') as f:
            assignments = json.load(f)
        assignments.append(assignment)
        with open(ASSIGNMENTS_FILE, 'w') as f:
            json.dump(assignments, f, indent=2)
        
        # Grade each submission
        graded_results = []
        for i, submission in enumerate(data['submissions']):
            if i < len(class_students):
                student = class_students[i]
                
                # Grade the submission using the existing grading logic
                try:
                    grade_result = grade_assignment(
                        data['assignment_type'],
                        submission,
                        data['rubric_content']
                    )
                    
                    # Create grade record
                    grade_record = {
                        "id": str(uuid.uuid4()),
                        "assignment_id": assignment_id,
                        "class_id": class_id,
                        "student_id": student['id'],
                        "student_name": student['name'],
                        "submission": submission,
                        "score": grade_result.get('score', 0),
                        "feedback": grade_result.get('feedback', ''),
                        "graded_at": datetime.now().isoformat()
                    }
                    
                    graded_results.append(grade_record)
                    
                except Exception as e:
                    print(f"Error grading submission for student {student['name']}: {str(e)}")
                    # Create a grade record with error
                    grade_record = {
                        "id": str(uuid.uuid4()),
                        "assignment_id": assignment_id,
                        "class_id": class_id,
                        "student_id": student['id'],
                        "student_name": student['name'],
                        "submission": submission,
                        "score": 0,
                        "feedback": f"Error grading submission: {str(e)}",
                        "graded_at": datetime.now().isoformat()
                    }
                    graded_results.append(grade_record)
        
        # Save all grades
        with open(GRADES_FILE, 'r') as f:
            grades = json.load(f)
        grades.extend(graded_results)
        with open(GRADES_FILE, 'w') as f:
            json.dump(grades, f, indent=2)
        
        # Update class statistics
        with open(CLASSES_FILE, 'r') as f:
            classes = json.load(f)
        
        for class_obj in classes:
            if class_obj['id'] == class_id:
                class_obj['assignment_count'] = len([a for a in assignments if a['class_id'] == class_id])
                class_obj['graded_count'] = len([g for g in grades if g['class_id'] == class_id])
                break
        
        with open(CLASSES_FILE, 'w') as f:
            json.dump(classes, f, indent=2)
            
        # Generate Excel file
        try:
            # Prepare summary data
            summary = {
                "total_files": len(graded_results),
                "processed": len([r for r in graded_results if "error" not in r]),
                "failed": len([r for r in graded_results if "error" in r]),
                "average_score": sum(float(r.get('score', 0)) for r in graded_results if "error" not in r and r.get('score') is not None) / 
                                max(1, len([r for r in graded_results if "error" not in r and r.get('score') is not None]))
            }
            
            # Use excel export module
            from excel_export import create_excel_for_batch_results, save_excel_file
            
            # Create Excel file
            excel_path, excel_filename = create_excel_for_batch_results(graded_results, summary, assignment.get('name', 'Batch Assignment'))
            
            # Save the Excel file to the exports directory
            export_dir = os.path.join(app.root_path, 'exports')
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            excel_path = save_excel_file(excel_path, excel_filename, export_dir)
            
            # Include the Excel file path in the response
            excel_url = url_for('download_excel_export', filename=excel_filename, _external=True)
            
            return jsonify({
                "success": True,
                "message": "Batch assignment graded successfully",
                "assignment": assignment,
                "results": graded_results,
                "excel_export": {
                    "filename": excel_filename,
                    "url": excel_url
                }
            }), 201
        except Exception as excel_error:
            print(f"Error generating Excel file: {str(excel_error)}")
            # Return results without Excel if there's an error
            return jsonify({
                "success": True,
                "message": "Batch assignment graded successfully (Excel export failed)",
                "assignment": assignment,
                "results": graded_results,
                "excel_export_error": str(excel_error)
            }), 201
        
    except Exception as e:
        print(f"Error processing batch assignment: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Failed to process batch assignment"
        }), 500

@app.route('/classes/<class_id>/batch-assignment', methods=['POST'])
def submit_batch_assignment_with_files(class_id):
    """Submit a batch assignment with file upload support"""
    try:
        # Get form data
        assignment_name = request.form.get('assignment_name')
        assignment_type = request.form.get('assignment_type')
        
        # Handle rubric - either file or text
        rubric_content = None
        if 'rubric_file' in request.files:
            rubric_file = request.files['rubric_file']
            if rubric_file.filename:
                # Extract text from rubric file
                rubric_content = extract_text_from_file(rubric_file.read(), rubric_file.filename)
        
        if not rubric_content:
            rubric_content = request.form.get('rubric_content', '')
        
        if not rubric_content:
            return jsonify({
                "success": False,
                "error": "Rubric content is required"
            }), 400
        
        # Load students for this class
        with open(STUDENTS_FILE, 'r') as f:
            students = json.load(f)
        
        class_students = [s for s in students if s['class_id'] == class_id]
        
        if not class_students:
            return jsonify({
                "success": False,
                "error": "No students found in this class"
            }), 400
        
        # Handle submissions - either files or text
        submissions = []
        
        if 'student_files' in request.files:
            # File upload mode with student mapping
            student_files = request.files.getlist('student_files')
            student_ids = request.form.getlist('student_ids')
            
            # Create submissions with student mapping
            for i, file in enumerate(student_files):
                if file.filename and i < len(student_ids):
                    # Extract text from file
                    extracted_text = extract_text_from_file(file.read(), file.filename)
                    submissions.append({
                        'content': extracted_text,
                        'student_id': student_ids[i]
                    })
        else:
            # Manual entry mode
            submissions_json = request.form.get('submissions')
            if submissions_json:
                text_submissions = json.loads(submissions_json)
                # Map to students in order
                for i, submission_text in enumerate(text_submissions):
                    if i < len(class_students):
                        submissions.append({
                            'content': submission_text,
                            'student_id': class_students[i]['id']
                        })
        
        if not submissions:
            return jsonify({
                "success": False,
                "error": "No submissions provided"
            }), 400
        
        # Create assignment record
        assignment_id = str(uuid.uuid4())
        assignment = {
            "id": assignment_id,
            "class_id": class_id,
            "name": assignment_name,
            "type": assignment_type,
            "rubric_content": rubric_content,
            "created_at": datetime.now().isoformat(),
            "total_submissions": len(submissions)
        }
        
        # Save assignment
        with open(ASSIGNMENTS_FILE, 'r') as f:
            assignments = json.load(f)
        assignments.append(assignment)
        with open(ASSIGNMENTS_FILE, 'w') as f:
            json.dump(assignments, f, indent=2)
        
        # Grade each submission
        graded_results = []
        for submission in submissions:
            # Find the student for this submission
            student = next((s for s in class_students if s['id'] == submission['student_id']), None)
            
            if student:
                try:
                    # Grade the submission
                    result = grade_assignment(
                        assignment_type=assignment_type,
                        submission=submission['content'],
                        rubric=rubric_content
                    )
                    
                    # Create grade record
                    grade_id = str(uuid.uuid4())
                    grade = {
                        "id": grade_id,
                        "assignment_id": assignment_id,
                        "student_id": student['id'],
                        "class_id": class_id,
                        "score": result['score'],
                        "feedback": result['feedback'],
                        "submission_text": submission['content'],
                        "graded_at": datetime.now().isoformat()
                    }
                    
                    # Save grade
                    with open(GRADES_FILE, 'r') as f:
                        grades = json.load(f)
                    grades.append(grade)
                    with open(GRADES_FILE, 'w') as f:
                        json.dump(grades, f, indent=2)
                    
                    graded_results.append({
                        "student_name": student['name'],
                        "student_id": student['id'],
                        "score": result['score'],
                        "feedback": result['feedback']
                    })
                    
                except Exception as e:
                    print(f"Error grading submission for student {student['name']}: {str(e)}")
                    graded_results.append({
                        "student_name": student['name'],
                        "student_id": student['id'],
                        "score": 0,
                        "feedback": f"Error grading submission: {str(e)}"
                    })
        
        return jsonify({
            "success": True,
            "assignment_id": assignment_id,
            "results": graded_results,
            "total_graded": len(graded_results)
        }), 200
        
    except Exception as e:
        print(f"Error in batch assignment: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Failed to process batch assignment with files"
        }), 500

@app.route('/api/students/<student_id>/details')
def get_student_details(student_id):
    """Get detailed information about a student including their grades"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        # Load student data
        with open(STUDENTS_FILE, 'r') as f:
            students = json.load(f)
        
        student = next((s for s in students if s['id'] == student_id), None)
        if not student:
            return jsonify({"success": False, "error": "Student not found"}), 404
            
        # Verify teacher owns the class this student belongs to
        with open(CLASSES_FILE, 'r') as f:
            classes = json.load(f)
        
        class_obj = next((c for c in classes if c['id'] == student['class_id']), None)
        if not class_obj or class_obj.get('teacher_id') != session['teacher_id']:
            return jsonify({"success": False, "error": "Access denied"}), 403
        
        # Load grades for this student
        with open(GRADES_FILE, 'r') as f:
            grades = json.load(f)
        
        student_grades = [g for g in grades if g['student_id'] == student_id]
        
        # Load assignments to get assignment names
        with open(ASSIGNMENTS_FILE, 'r') as f:
            assignments = json.load(f)
        
        # Combine grade data with assignment info
        detailed_grades = []
        for grade in student_grades:
            assignment = next((a for a in assignments if a['id'] == grade['assignment_id']), None)
            detailed_grades.append({
                "grade_id": grade['id'],
                "assignment_name": assignment['name'] if assignment else "Unknown Assignment",
                "assignment_type": assignment['type'] if assignment else "Unknown",
                "score": grade['score'],
                "feedback": grade['feedback'],
                "graded_at": grade['graded_at']
            })
        
        return jsonify({
            "success": True,
            "student": student,
            "grades": detailed_grades
        })
        
    except Exception as e:
        print(f"Error getting student details: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/assignments/<assignment_id>/details')
def get_assignment_details(assignment_id):
    """Get detailed information about an assignment including all student submissions"""
    try:
        # Load assignment data
        with open(ASSIGNMENTS_FILE, 'r') as f:
            assignments = json.load(f)
        
        assignment = next((a for a in assignments if a['id'] == assignment_id), None)
        if not assignment:
            return jsonify({"success": False, "error": "Assignment not found"}), 404
        
        # Load grades for this assignment
        with open(GRADES_FILE, 'r') as f:
            grades = json.load(f)
        
        assignment_grades = [g for g in grades if g['assignment_id'] == assignment_id]
        
        # Load students to get student names
        with open(STUDENTS_FILE, 'r') as f:
            students = json.load(f)
        
        # Combine grade data with student info
        detailed_submissions = []
        for grade in assignment_grades:
            student = next((s for s in students if s['id'] == grade['student_id']), None)
            detailed_submissions.append({
                "grade_id": grade['id'],
                "student_name": student['name'] if student else "Unknown Student",
                "student_id": grade['student_id'],
                "score": grade['score'],
                "feedback": grade['feedback'],
                "submission_text": grade['submission_text'],
                "graded_at": grade['graded_at']
            })
        
        return jsonify({
            "success": True,
            "assignment": assignment,
            "submissions": detailed_submissions
        })
        
    except Exception as e:
        print(f"Error getting assignment details: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/classes/<class_id>/grades', methods=['GET'])
def get_class_grades(class_id):
    """Get all grades for a class"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    # Verify teacher owns this class
    try:
        with open(CLASSES_FILE, 'r') as f:
            classes = json.load(f)
        
        class_obj = next((c for c in classes if c['id'] == class_id), None)
        if not class_obj or class_obj.get('teacher_id') != session['teacher_id']:
            return jsonify({"error": "Class not found or access denied"}), 403
        
        with open(GRADES_FILE, 'r') as f:
            grades = json.load(f)
        
        class_grades = [g for g in grades if g['class_id'] == class_id]
        return jsonify(class_grades), 200
    except Exception as e:
        print(f"Error loading grades: {str(e)}")
        return jsonify({"error": "Failed to load grades"}), 500

@app.route('/students/<student_id>/grades', methods=['GET'])
def get_student_grades(student_id):
    """Get all grades for a specific student"""
    try:
        with open(GRADES_FILE, 'r') as f:
            grades = json.load(f)
        
        student_grades = [g for g in grades if g['student_id'] == student_id]
        return jsonify(student_grades), 200
    except Exception as e:
        print(f"Error loading student grades: {str(e)}")
        return jsonify({"error": "Failed to load student grades"}), 500

@app.route('/classes/students.json', methods=['GET'])
def get_all_students_json():
    """Get all students as JSON (for frontend compatibility)"""
    try:
        with open(STUDENTS_FILE, 'r') as f:
            students = json.load(f)
        return jsonify(students), 200
    except Exception as e:
        print(f"Error loading students: {str(e)}")
        return jsonify({"error": "Failed to load students"}), 500

@app.route('/classes/assignments.json', methods=['GET'])
def get_all_assignments_json():
    """Get all assignments as JSON (for frontend compatibility)"""
    try:
        with open(ASSIGNMENTS_FILE, 'r') as f:
            assignments = json.load(f)
        return jsonify(assignments), 200
    except Exception as e:
        print(f"Error loading assignments: {str(e)}")
        return jsonify({"error": "Failed to load assignments"}), 500

@app.route('/login', methods=['POST'])
def login_post():
    """
    Handle teacher ID login
    """
    try:
        data = request.get_json()
        teacher_id = data.get('teacher_id')
        
        if not teacher_id:
            return jsonify({
                'success': False,
                'error': 'Teacher ID is required'
            }), 400
        
        if teacher_id not in VALID_TEACHER_IDS:
            return jsonify({
                'success': False,
                'error': 'Invalid Teacher ID'
            }), 401
        
        # Store teacher ID in session
        session['teacher_id'] = teacher_id
        session['teacher_name'] = VALID_TEACHER_IDS[teacher_id]['name']
        
        return jsonify({
            'success': True,
            'teacher_id': teacher_id,
            'teacher_name': VALID_TEACHER_IDS[teacher_id]['name']
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Login failed'
        }), 500

@app.route('/logout', methods=['POST'])
def logout():
    """
    Handle logout
    """
    session.clear()
    return jsonify({'success': True}), 200

@app.route('/current-teacher', methods=['GET'])
def current_teacher():
    """
    Get current logged-in teacher info
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    return jsonify({
        'teacher_id': session['teacher_id'],
        'teacher_name': session['teacher_name']
    }), 200

@app.route('/exports/<filename>')
def download_excel_export(filename):
    """
    Download an Excel export file
    """
    export_dir = os.path.join(app.root_path, 'exports')
    file_path = os.path.join(export_dir, filename)
    
    try:
        if not os.path.exists(file_path):
            print(f"Excel file not found: {file_path}")
            return jsonify({"error": "Excel file not found"}), 404
        
        if os.path.getsize(file_path) == 0:
            print(f"Excel file is empty: {file_path}")
            return jsonify({"error": "Excel file is empty"}), 500
            
        print(f"Sending Excel file: {file_path}")
        return send_file(file_path,
                        download_name=filename,
                        as_attachment=True,
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        print(f"Error sending Excel file: {str(e)}")
        return jsonify({"error": f"Failed to download Excel file: {str(e)}"}), 500

@app.route('/')
def login():
    """
    Login page route.
    """
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """
    Main dashboard route - requires authentication
    """
    if 'teacher_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

if __name__ == '__main__':
    print(f"Starting server on {Config.HOST}:{Config.PORT}")
    print(f"Debug mode: {Config.DEBUG}")
    try:
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()