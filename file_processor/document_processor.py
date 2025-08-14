import os
import tempfile
import platform
import shutil
from typing import Union
import io

def _get_poppler_path():
    """
    Cross-platform function to detect Poppler installation.
    Returns the path to Poppler binaries or None if not found.
    """
    # First, try manual configuration
    try:
        from poppler_config import get_manual_poppler_path
        manual_path = get_manual_poppler_path()
        if manual_path:
            print(f"Using manually configured Poppler at: {manual_path}")
            return manual_path
    except ImportError:
        pass  # poppler_config.py not found, continue with auto-detection
    
    system = platform.system().lower()
    
    # Second, check if poppler binaries are in system PATH
    if shutil.which('pdftoppm'):
        return None  # Use system PATH
    
    # Platform-specific paths
    if system == 'windows':
        # Windows search paths
        search_paths = [
            r"C:\Program Files\poppler\bin",
            r"C:\Program Files (x86)\poppler\bin",
            r"C:\poppler\bin",
            r"C:\tools\poppler\bin",
            # Virtual environment paths
            os.path.join(os.environ.get('VIRTUAL_ENV', ''), 'Library', 'bin'),
            os.path.join(os.environ.get('CONDA_PREFIX', ''), 'Library', 'bin'),
        ]
        binary_name = 'pdftoppm.exe'
    elif system == 'darwin':  # macOS
        search_paths = [
            "/opt/homebrew/bin",      # Apple Silicon Homebrew
            "/usr/local/bin",         # Intel Homebrew
            "/opt/local/bin",         # MacPorts
        ]
        binary_name = 'pdftoppm'
    else:  # Linux
        search_paths = [
            "/usr/bin",
            "/usr/local/bin",
        ]
        binary_name = 'pdftoppm'
    
    # Check each path
    for path in search_paths:
        if path and os.path.exists(path):
            binary_path = os.path.join(path, binary_name)
            if os.path.exists(binary_path):
                print(f"Found Poppler at: {path}")
                return path
    
    return None

def _get_platform_install_instructions():
    """
    Get installation instructions for the current platform.
    """
    system = platform.system().lower()
    
    if system == 'windows':
        return """
Windows Installation:
1. Download from: https://github.com/oschwartz10612/poppler-windows/releases/
2. Extract to C:\\poppler
3. Add C:\\poppler\\bin to your PATH
4. Or use conda: conda install -c conda-forge poppler"""
    elif system == 'darwin':
        return """
macOS Installation:
1. Using Homebrew: brew install poppler
2. Using conda: conda install -c conda-forge poppler"""
    else:
        return """
Linux Installation:
1. Ubuntu/Debian: sudo apt-get install poppler-utils
2. Using conda: conda install -c conda-forge poppler"""

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extract text from various file formats including TXT, PDF, DOC, DOCX, and image files.
    
    Args:
        file_content (bytes): The file content as bytes
        filename (str): The original filename to determine file type
        
    Returns:
        str: The extracted text from the file
    """
    try:
        # Get file extension
        file_ext = os.path.splitext(filename.lower())[1]
        
        if file_ext == '.txt':
            return _extract_text_from_txt(file_content)
        elif file_ext == '.pdf':
            return _extract_text_from_pdf(file_content)
        elif file_ext in ['.doc', '.docx']:
            return _extract_text_from_word(file_content, file_ext)
        elif file_ext in ['.jpg', '.jpeg', '.png']:
            return _extract_text_from_image_file(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
            
    except Exception as e:
        return f"[FILE PROCESSING ERROR: {str(e)}]"

def _extract_text_from_txt(file_content: bytes) -> str:
    """
    Extract text from a TXT file.
    """
    try:
        # Try UTF-8 first, then fallback to other encodings
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return file_content.decode('latin-1')
            except UnicodeDecodeError:
                return file_content.decode('utf-8', errors='ignore')
    except Exception as e:
        raise Exception(f"Failed to extract text from TXT file: {str(e)}")

def _extract_text_from_pdf_with_ocr(file_content: bytes) -> str:
    """
    Extract text from a PDF file using OCR (pdf2image + GPT-4 Vision) as fallback.
    Cross-platform compatible.
    """
    try:
        from pdf2image import convert_from_bytes
        from image_processor.ocr import extract_text_from_image
        
        print("Converting PDF to images for OCR processing...")
        
        # Get cross-platform Poppler path
        poppler_path = _get_poppler_path()
        
        # Try to convert PDF pages to images
        try:
            if poppler_path:
                print(f"Using Poppler at: {poppler_path}")
                images = convert_from_bytes(file_content, dpi=200, fmt='PNG', poppler_path=poppler_path)
            else:
                print("Using Poppler from system PATH")
                images = convert_from_bytes(file_content, dpi=200, fmt='PNG')
        except Exception as poppler_error:
            print(f"Failed to convert PDF to images: {poppler_error}")
            install_instructions = _get_platform_install_instructions()
            return f"[OCR PROCESSING ERROR: Could not convert PDF pages to images. {poppler_error}. Please install Poppler:{install_instructions}]"
        
        if not images:
            return "[OCR PROCESSING ERROR: Could not convert PDF pages to images]"
        
        print(f"Converted PDF to {len(images)} image(s)")
        
        # Extract text from each page using OCR
        all_text = []
        for i, image in enumerate(images):
            print(f"Processing page {i + 1} with OCR...")
            
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # Extract text using GPT-4 Vision OCR
            try:
                page_text = extract_text_from_image(img_bytes)
                print(f"Page {i + 1} OCR result: {page_text[:100]}..." if len(page_text) > 100 else f"Page {i + 1} OCR result: {page_text}")
                
                if page_text and not page_text.startswith('[No text detected') and not page_text.startswith('Error'):
                    all_text.append(f"--- Page {i + 1} ---\n{page_text}")
                    print(f"Page {i + 1}: Extracted {len(page_text)} characters via OCR")
                else:
                    print(f"Page {i + 1}: No text detected via OCR - {page_text}")
            except Exception as ocr_error:
                print(f"Page {i + 1}: OCR failed with error: {ocr_error}")
                continue
        
        if not all_text:
            return "[OCR PROCESSING WARNING: No text could be extracted from any page of the PDF using OCR. The document may not contain readable text.]"
        
        combined_text = "\n\n".join(all_text)
        print(f"Total OCR text extracted: {len(combined_text)} characters")
        
        return combined_text
        
    except ImportError as e:
        if "pdf2image" in str(e):
            return "[OCR PROCESSING ERROR: pdf2image library not installed. Cannot perform OCR on PDF.]"
        elif "image_processor" in str(e):
            return "[OCR PROCESSING ERROR: OCR module not available.]"
        else:
            return f"[OCR PROCESSING ERROR: Missing dependency - {str(e)}]"
    except Exception as e:
        error_msg = str(e)
        print(f"Error in PDF OCR processing: {error_msg}")
        
        # Check for specific Poppler error
        if "poppler" in error_msg.lower() or "unable to get page count" in error_msg.lower():
            install_instructions = _get_platform_install_instructions()
            return f"[OCR PROCESSING ERROR: Poppler is required for PDF to image conversion but is not installed or accessible.{install_instructions} Alternatively, try uploading your document as individual image files (PNG/JPG) which can be processed directly.]"
        
        return f"[OCR PROCESSING ERROR: {error_msg}]"

def _extract_text_from_pdf_vision_first(file_content: bytes) -> str:
    """
    Extract text from a PDF file using GPT-4 Vision as the PRIMARY method,
    bypassing PyPDF2 entirely for better results.
    """
    try:
        from pdf2image import convert_from_bytes
        from image_processor.ocr import extract_text_from_image
        
        print("Using GPT-4 Vision as PRIMARY PDF processing method...")
        
        # Get cross-platform Poppler path
        poppler_path = _get_poppler_path()
        
        # Convert PDF pages to images
        try:
            if poppler_path:
                print(f"Using Poppler at: {poppler_path}")
                images = convert_from_bytes(file_content, dpi=300, fmt='PNG', poppler_path=poppler_path)  # Higher DPI for better quality
            else:
                print("Using Poppler from system PATH")
                images = convert_from_bytes(file_content, dpi=300, fmt='PNG')
        except Exception as poppler_error:
            print(f"Failed to convert PDF to images: {poppler_error}")
            install_instructions = _get_platform_install_instructions()
            return f"[PDF PROCESSING ERROR: Could not convert PDF pages to images. {poppler_error}. Please install Poppler:{install_instructions}]"
        
        if not images:
            return "[PDF PROCESSING ERROR: Could not convert PDF pages to images]"
        
        print(f"Successfully converted PDF to {len(images)} image(s) for GPT-4 Vision processing")
        
        # Process each page with GPT-4 Vision
        all_text = []
        for i, image in enumerate(images):
            print(f"Processing page {i + 1} with GPT-4 Vision...")
            
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # Extract text using GPT-4 Vision with enhanced prompt
            try:
                page_text = extract_text_from_image(img_bytes, assignment_type="document")
                print(f"Page {i + 1} GPT-4 Vision result: {len(page_text)} characters extracted")
                
                if page_text and not page_text.startswith('[No text detected') and not page_text.startswith('Error'):
                    all_text.append(f"--- Page {i + 1} ---\n{page_text}")
                    print(f"Page {i + 1}: Successfully processed with GPT-4 Vision")
                else:
                    print(f"Page {i + 1}: No meaningful text detected - {page_text[:100]}...")
            except Exception as vision_error:
                print(f"Page {i + 1}: GPT-4 Vision failed with error: {vision_error}")
                all_text.append(f"--- Page {i + 1} ---\n[GPT-4 Vision processing failed: {str(vision_error)}]")
                continue
        
        if not all_text:
            return "[PDF PROCESSING ERROR: GPT-4 Vision could not extract text from any page of the PDF. The document may not contain readable content.]"
        
        combined_text = "\n\n".join(all_text)
        print(f"Total GPT-4 Vision text extracted: {len(combined_text)} characters")
        
        return combined_text
        
    except ImportError as e:
        if "pdf2image" in str(e):
            return "[PDF PROCESSING ERROR: pdf2image library not installed. Cannot perform GPT-4 Vision processing on PDF.]"
        elif "image_processor" in str(e):
            return "[PDF PROCESSING ERROR: OCR module not available.]"
        else:
            return f"[PDF PROCESSING ERROR: Missing dependency - {str(e)}]"
    except Exception as e:
        error_msg = str(e)
        print(f"Error in GPT-4 Vision PDF processing: {error_msg}")
        
        # Check for specific Poppler error
        if "poppler" in error_msg.lower() or "unable to get page count" in error_msg.lower():
            install_instructions = _get_platform_install_instructions()
            return f"[PDF PROCESSING ERROR: Poppler is required for PDF to image conversion but is not installed or accessible.{install_instructions} Alternatively, try uploading your document as individual image files (PNG/JPG) which can be processed directly.]"
        
        return f"[PDF PROCESSING ERROR: {error_msg}]"

def _extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from a PDF file using GPT-4 Vision as PRIMARY method,
    with PyPDF2 as fallback only if Vision fails.
    """
    # Try GPT-4 Vision first
    print("Attempting GPT-4 Vision processing for PDF...")
    vision_result = _extract_text_from_pdf_vision_first(file_content)
    
    # If Vision was successful, return the result
    if not vision_result.startswith('[PDF PROCESSING ERROR'):
        print("GPT-4 Vision PDF processing successful!")
        return vision_result
    
    # Only fall back to PyPDF2 if Vision completely failed
    print("GPT-4 Vision failed, attempting PyPDF2 fallback...")
    
    try:
        import PyPDF2
        import io
        
        # Create a file-like object from bytes
        pdf_file = io.BytesIO(file_content)
        
        # Create PDF reader
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            print(f"Page {page_num + 1}: Extracted {len(page_text)} characters")
            text += page_text + "\n"
        
        print(f"Total PyPDF2 text extracted: {len(text)} characters")
        
        # Check if we extracted meaningful content
        if len(text.strip()) < 50:
            print("PyPDF2 also extracted insufficient text...")
            return f"[PDF PROCESSING WARNING: Both GPT-4 Vision and PyPDF2 failed to extract meaningful content. Vision error: {vision_result}. PyPDF2 extracted only {len(text.strip())} characters: {text.strip()}]"
        
        return text.strip()
        
    except ImportError:
        return f"[PDF PROCESSING ERROR: Both GPT-4 Vision and PyPDF2 failed. Vision error: {vision_result}. PyPDF2 not available.]"
    except Exception as e:
        return f"[PDF PROCESSING ERROR: Both GPT-4 Vision and PyPDF2 failed. Vision error: {vision_result}. PyPDF2 error: {str(e)}]"

def _extract_text_from_word(file_content: bytes, file_ext: str) -> str:
    """
    Extract text from DOC/DOCX files using python-docx.
    """
    try:
        if file_ext == '.docx':
            return _extract_text_from_docx(file_content)
        elif file_ext == '.doc':
            # For .doc files, we'll use a fallback approach
            # Note: python-docx doesn't support .doc files directly
            raise Exception(".doc files are not directly supported. Please convert to .docx format or use .txt/.pdf instead.")
        else:
            raise ValueError(f"Unsupported Word file type: {file_ext}")
            
    except Exception as e:
        raise Exception(f"Failed to extract text from Word file: {str(e)}")

def _extract_text_from_docx(file_content: bytes) -> str:
    """
    Extract text from a DOCX file using python-docx.
    """
    try:
        from docx import Document
        import io
        
        # Create a file-like object from bytes
        docx_file = io.BytesIO(file_content)
        
        # Load the document
        doc = Document(docx_file)
        
        # Extract text from all paragraphs
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
            
        return text.strip()
        
    except ImportError:
        raise Exception("python-docx library is required for DOCX processing. Please install it with: pip install python-docx")
    except Exception as e:
        raise Exception(f"Failed to extract text from DOCX file: {str(e)}")

def _extract_text_from_image_file(file_content: bytes) -> str:
    """
    Extract text from image files using OCR.
    
    Args:
        file_content (bytes): The image file content as bytes
        
    Returns:
        str: The extracted text from the image
    """
    try:
        # Import OCR function
        from image_processor.ocr import extract_text_from_image
        
        # Pass raw bytes directly to the OCR function
        # The extract_text_from_image function handles base64 conversion internally
        result = extract_text_from_image(file_content)
        
        # The OCR function returns a string directly
        return str(result)
            
    except Exception as e:
        raise Exception(f"Failed to extract text from image file: {str(e)}")