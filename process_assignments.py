import os
import sys
from image_processor.ocr import extract_text_from_image, detect_diagrams_in_image
from grader import grade_assignment
from grader.engine import grade_assignment_with_vision
from config import Config

def main():
    # Default rubric - you can modify this to suit your needs
    default_rubric = """Grade on a scale of 0-100 based on:
    1. Content accuracy (40%)
    2. Organization and structure (30%)
    3. Clarity of expression (20%)
    4. Grammar and mechanics (10%)
    """
    
    # Default assignment type
    assignment_type = "Essay"
    
    # Get the assignment folder from config
    assignment_folder = Config.ASSIGNMENT_FOLDER
    
    # Check if the assignment folder exists
    if not os.path.exists(assignment_folder):
        print(f"Assignment folder '{assignment_folder}' does not exist.")
        print("Please create the folder and add some image files to process.")
        return
    
    # Get all image files in the assignment folder
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
    image_files = []
    
    for filename in os.listdir(assignment_folder):
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            image_files.append(filename)
    
    if not image_files:
        print(f"No image files found in '{assignment_folder}'.")
        print(f"Supported formats: {', '.join(image_extensions)}")
        return
    
    print(f"Found {len(image_files)} image file(s) to process.")
    print(f"Assignment type: {assignment_type}")
    print(f"Rubric: {default_rubric}")
    print("-" * 50)
    
    # Process each image file
    for filename in image_files:
        try:
            print(f"\nProcessing: {filename}")
            
            # Read the image file
            file_path = os.path.join(assignment_folder, filename)
            with open(file_path, 'rb') as f:
                image_bytes = f.read()
            
            # Detect diagrams
            print("Detecting diagrams...")
            diagram_info = detect_diagrams_in_image(image_bytes)
            print(f"Diagram detection: {diagram_info}")
            
            # Route to appropriate grading method
            if diagram_info.get('has_diagrams', False) and diagram_info.get('confidence') in ['high', 'medium']:
                print("Using GPT-4 Vision for diagram analysis...")
                try:
                    result = grade_assignment_with_vision(assignment_type, image_bytes, default_rubric, diagram_info)
                    processing_method = "GPT-4 Vision (Diagram Analysis)"
                except Exception as vision_error:
                    print(f"GPT-4 Vision failed: {str(vision_error)}")
                    print("Falling back to standard process...")
                    extracted_text = extract_text_from_image(image_bytes, assignment_type)
                    result = grade_assignment(assignment_type, extracted_text, default_rubric)
                    processing_method = "Standard OCR + Gemini (Fallback)"
            else:
                print("Using standard OCR + text grading...")
                extracted_text = extract_text_from_image(image_bytes, assignment_type)
                
                if not extracted_text or len(extracted_text.strip()) < 10:
                    print("Warning: Little or no text extracted from the image.")
                    print("Text extracted:", extracted_text)
                    continue
                
                result = grade_assignment(assignment_type, extracted_text, default_rubric)
                processing_method = "Standard OCR + Gemini"
            
            # Display the results
            print("\nGRADING RESULTS:")
            print(f"Processing Method: {processing_method}")
            print(f"Score: {result['score']}")
            print(f"Feedback: {result['feedback']}")
            if 'extracted_text' in locals():
                print("\nExtracted Text:")
                print(extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text)
            print("\n" + "-"*50 + "\n")
                
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            print("-"*50 + "\n")
    
    print("Processing complete!")

if __name__ == "__main__":
    main()