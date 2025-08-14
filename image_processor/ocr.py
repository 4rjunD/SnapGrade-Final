from openai import OpenAI
import base64
import json
import re
from config import Config

def detect_diagrams_in_image(image_data):
    """
    Detect if an image contains diagrams, charts, MCQ, or visual elements that require GPT-4 Vision.
    
    Args:
        image_data (bytes): The image data as bytes
        
    Returns:
        dict: Contains 'has_diagrams' (bool) and 'diagram_types' (list)
    """
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Convert image data to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Enhanced prompt to detect MCQ and question types
        prompt = """Analyze this image and determine if it contains any of the following visual elements that require GPT-4 Vision for optimal grading:

**VISUAL CONTENT TYPES:**
1. **Multiple Choice Questions (MCQ)** - Questions with A/B/C/D options, bubbles, checkboxes
2. **Mathematical diagrams** - Graphs, charts, geometric figures, coordinate planes, equations with symbols
3. **Scientific diagrams** - Molecular structures, circuit diagrams, biological illustrations, lab setups
4. **Technical drawings** - Engineering schematics, architectural plans, technical illustrations
5. **Data visualizations** - Bar charts, pie charts, line graphs, tables with visual elements
6. **Maps or geographical content** - Any geographical illustrations, maps, location-based questions
7. **Flow charts or process diagrams** - Decision trees, workflow diagrams, organizational charts
8. **Visual problem sets** - Math problems with visual components, physics diagrams, chemistry structures
9. **Formatted questionnaires** - Structured forms, surveys, answer sheets with visual layout
10. **Any content where visual layout/formatting is crucial for understanding**

**IMPORTANT:** If the image contains:
- Multiple choice questions (even if just text-based)
- Mathematical equations with special symbols or formatting
- Any structured visual layout that affects comprehension
- Charts, graphs, or diagrams of any kind
- Answer sheets or forms with specific formatting

Then set has_diagrams to TRUE.

Only set has_diagrams to FALSE if the image contains purely plain text without any visual structure, formatting, or question layouts.

Respond in JSON format:
{
    "has_diagrams": true/false,
    "diagram_types": ["list of specific types found"],
    "confidence": "high/medium/low",
    "description": "brief description of visual content and why it needs vision processing"
}"""
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model=Config.OPENAI_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        # Parse the response
        result_text = response.choices[0].message.content.strip()
        
        # Clean JSON response if needed
        if result_text.startswith('```json'):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith('```'):
            result_text = result_text[3:-3].strip()
            
        result = json.loads(result_text)
        
        return {
            'has_diagrams': result.get('has_diagrams', False),
            'diagram_types': result.get('diagram_types', []),
            'confidence': result.get('confidence', 'low'),
            'description': result.get('description', '')
        }
        
    except Exception as e:
        print(f"Error in diagram detection: {str(e)}")
        # Default to no diagrams on error to maintain standard flow
        return {
            'has_diagrams': False,
            'diagram_types': [],
            'confidence': 'low',
            'description': 'Error in detection'
        }

def extract_text_from_image(image_data, assignment_type=None):
    """
    Extract text from an image using OpenAI's GPT-4 Vision API.
    Enhanced for document processing and assignment grading.
    Optimized to carefully identify student information at the top of pages.
    """
    try:
        # Print debug information
        print("Starting GPT-4 Vision OCR process...")
        
        # Check if image_data is valid
        if not image_data or len(image_data) == 0:
            raise ValueError("Empty image data provided")
            
        print(f"Image data size: {len(image_data)} bytes")
        print(f"Assignment type: {assignment_type}")
        
        # Initialize OpenAI client
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Convert image data to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Create enhanced prompts for document processing
        if assignment_type == "document":
            prompt = """Please analyze this document image and extract ALL text content with maximum accuracy, with special attention to the top of the page where student information appears.

**STUDENT IDENTIFICATION - HIGHEST PRIORITY:**
1. Examine the TOP of the document FIRST, especially top corners, headers and margins
2. Look for any text that appears to be a student name:
   - "Name: [Student Name]" or just "[Student Name]" at the top
   - Any text that appears to be a full name at the top of the document
3. Place this information at the beginning of your response
4. Include the student name even if it's just a name without any label

**DOCUMENT PROCESSING INSTRUCTIONS:**
1. Extract every piece of text visible in the document
2. Maintain the original structure and formatting as much as possible
3. Include headers, body text, mathematical expressions, and any annotations
4. For handwritten content, provide your best interpretation
5. For mathematical work, extract all steps, calculations, and final answers
6. For multiple choice questions, identify both the questions and any selected answers
7. Be extremely thorough - this is for academic grading purposes

**FORMATTING GUIDELINES:**
- Begin with any student information found at the top of the document
- Preserve paragraph breaks and section divisions
- Use clear headings for different sections
- Mark mathematical expressions clearly
- Indicate any unclear or ambiguous text with [unclear: best guess]

Extract ALL visible text from this document image:"""
        elif assignment_type and assignment_type.lower() in ['multiple choice', 'problem set', 'math', 'mathematics', 'calculus', 'algebra', 'geometry', 'statistics']:
            # Use existing enhanced prompt for assignments
            prompt = """Please analyze this image and extract all text content with special attention to OCR accuracy, student identification, and student work.

**STUDENT IDENTIFICATION - HIGHEST PRIORITY:**
1. Look CAREFULLY at the top of the page for the student's name, especially in corners
2. Common formats include:
   - "Name: [Student Name]" or just "[Student Name]" at top left or right
   - Any text that appears to be a full name at the top of the document
3. Include this information FIRST in your response, even without explicit labels
4. Even if the name is handwritten and somewhat unclear, include your best interpretation

**CRITICAL OCR INSTRUCTIONS:**
1. Be very forgiving of handwriting variations and unclear text
2. When text is ambiguous, provide your best interpretation in brackets [like this]
3. Pay special attention to mathematical symbols, numbers, and final answers
4. For multiple-choice questions, carefully identify student selections (bubbled circles, checkmarks, circled letters)

**MULTIPLE CHOICE DETECTION:**
For each multiple-choice question you find:
1. Extract the question text (be forgiving of OCR errors)
2. List all answer choices (A, B, C, D, etc.)
3. Identify which answer(s) the student selected (look for any marking: bubbles, checks, circles, underlines)
4. Note the question number if visible

**WORK ANALYSIS:**
For mathematical work shown:
1. Extract all visible steps and calculations
2. Identify final answers clearly
3. Note any partially visible or unclear work
4. Be generous in interpreting mathematical notation

Format your response as:
- First, provide any student identification information (name) that you find
- Next, provide all the extracted text as it appears
- Then add:

[OCR CONFIDENCE NOTE: This text was extracted with OCR error tolerance. Some characters may be interpreted from unclear handwriting.]

[MULTIPLE CHOICE ANALYSIS] (if applicable)
Question 1: [question text]
Choices: A) [choice A], B) [choice B], C) [choice C], D) [choice D]
Student Selected: [letter(s) that appear to be marked]

[FINAL ANSWERS DETECTED]
- Problem 1: [final answer]
- Problem 2: [final answer]
...

If no text is found, respond with '[No text detected in the image]'."""
        else:
            # Use existing general prompt
            prompt = """Please extract all text from this image with MAXIMUM OCR error tolerance, focusing on student identification and content.

**STUDENT IDENTIFICATION - HIGHEST PRIORITY:**
1. Carefully inspect the TOP of the document, especially CORNERS, for the student name
2. Common formats include:
   - "Name: [Student Name]" or just "[Student Name]" at top left or right
   - Any text that appears to be a person's name at the top of the document
3. Even if there's no label explicitly saying "Name", if you see what looks like a name, include it
4. The student name is almost always one of the first text elements on the page

**ULTRA-LENIENT INSTRUCTIONS:**
1. PRIORITIZE identifying student information first, then final answers or conclusions
2. Be extremely forgiving of unclear handwriting
3. Guess at ambiguous text and mark with [interpreted: text]
4. Focus on extracting key content rather than perfect formatting
5. Look for answer patterns and important conclusions

Format your response as:
[STUDENT INFORMATION]
Name: [Student name if found, or "Not clearly identified"]
Assignment: [Title or topic if identifiable]

[EXTRACTED TEXT - with maximum leniency]

[KEY ANSWERS/CONCLUSIONS DETECTED]
- [any identifiable final answers or main points]

[OCR CONFIDENCE NOTE: This extraction uses maximum leniency for unclear text.]"""
        
        print("Sending request to GPT-4 Vision...")
        
        # Call the OpenAI API with vision capabilities
        response = client.chat.completions.create(
            model=Config.OPENAI_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2500,  # Increased for detailed analysis
            temperature=0.1  # Low temperature for consistent extraction
        )
        
        # Extract the response content
        extracted_text = response.choices[0].message.content.strip()
        
        print("Text extraction complete using GPT-4 Vision")
        
        # If no text was extracted, return a message
        if not extracted_text or extracted_text.lower() == "[no text detected in the image]":
            return "[No text detected in the image. Please ensure the image contains clear, readable text.]"
            
        return extracted_text
        
    except Exception as e:
        print(f"Error in GPT-4 Vision OCR: {str(e)}")
        # Fallback error message
        if "model" in str(e).lower() and "vision" in str(e).lower():
            return "GPT-4 Vision model is not available. Please check your OpenAI API access."
        raise Exception(f"Error extracting text from image using GPT-4 Vision: {str(e)}")


def extract_corner_text(image_data):
    """
    Specialized function to extract text specifically from the corners of an image,
    which is where student names are typically found.
    
    Args:
        image_data (bytes): The image data as bytes
        
    Returns:
        dict: Contains text extracted from each corner
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Convert image data to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Create a specialized prompt focusing only on corner text
        prompt = """Focus ONLY on the FOUR CORNERS of this image and extract any text found there.

CRITICAL INSTRUCTIONS:
1. ONLY look at the four corner regions (top-left, top-right, bottom-left, bottom-right)
2. Student names are most often in the top-left or top-right corners
3. Extract ANY text found in these corners, even if it's just a few words
4. For each corner, report exactly what text appears there, if any
5. If handwritten, provide your best interpretation
6. Do not analyze the main content of the document

Format your response in this exact JSON structure:
{
    "top_left": "text found in top left corner or null if none",
    "top_right": "text found in top right corner or null if none",
    "bottom_left": "text found in bottom left corner or null if none",
    "bottom_right": "text found in bottom right corner or null if none"
}"""
        
        # Call GPT-4 Vision for corner analysis only
        response = client.chat.completions.create(
            model=Config.OPENAI_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        # Parse response
        content = response.choices[0].message.content.strip() if response.choices[0].message.content else "{}"
        
        # Clean JSON response if needed
        if content.startswith('```json'):
            content = content[7:-3].strip()
        elif content.startswith('```'):
            content = content[3:-3].strip()
            
        result = json.loads(content)
        return result
        
    except Exception as e:
        print(f"Error extracting corner text: {str(e)}")
        return {
            "top_left": None,
            "top_right": None,
            "bottom_left": None,
            "bottom_right": None,
            "error": str(e)
        }

def extract_student_name_from_text(extracted_text):
    """
    Extract student name from OCR text using pattern matching and AI assistance.
    Optimized to find student names typically written at top corners of assignments.
    
    Args:
        extracted_text (str): The text extracted from the assignment
        
    Returns:
        dict: Contains 'student_name' (str or None) and 'confidence' (str)
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Use AI to extract student name from the text
        prompt = f"""Analyze the following text extracted from a student assignment and identify the student's name.

CRITICAL INSTRUCTIONS:
1. Student names are MOST OFTEN found in these locations:
   - Top right corner of the first page
   - Top left corner of the first page
   - Header area of the assignment
   - First few lines of the document

2. Look for these common patterns:
   - "Name: [Student Name]"
   - "[Student Name]" (just a name by itself at the top)
   - "Student: [Student Name]"
   - "By: [Student Name]"
   - First Name Last Name (format that appears to be a name)
   - Any text pattern that is clearly a person's name

3. Be VERY FLEXIBLE with name extraction:
   - If you see what looks like a name at the top of a document, extract it even without explicit labels
   - A name is typically 1-3 words and usually includes a first and last name
   - Names can be with or without middle initials
   - The name is often the first non-title text at the top of the assignment

4. For handwritten assignments:
   - Names may be written less formally
   - If something looks like a name at the top of the page, it's very likely the student's name

Text to analyze (first portion of assignment):
{extracted_text[:1500]}

Respond in JSON format:
{{
    "student_name": "Full Name" or null if no name found,
    "confidence": "high" | "medium" | "low",
    "location": "Description of where the name was found"
}}

If no clear student name is found, return null for student_name."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content.strip())
        return result
        
    except Exception as e:
        print(f"Error extracting student name: {str(e)}")
        return {
            "student_name": None,
            "confidence": "low",
            "location": "Error occurred during name extraction"
        }

def extract_assignment_title_from_text(extracted_text):
    """
    Extract assignment title from OCR text using pattern matching and AI assistance.
    
    Args:
        extracted_text (str): The text extracted from the assignment
        
    Returns:
        dict: Contains 'assignment_title' (str or None) and 'confidence' (str)
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Use AI to extract assignment title from the text
        prompt = f"""Analyze the following text extracted from a student assignment and identify the assignment title.

Look for patterns like:
- "Assignment: [Title]"
- "Title: [Title]"
- "Subject: [Subject]"
- "Topic: [Topic]"
- "Chapter: [Chapter]" 
- "Unit: [Unit]"
- "Homework #[Number]" or "Quiz #[Number]"
- Bold or underlined text at the top that appears to be a title
- Any clear indication of what this assignment is about

Text to analyze:
{extracted_text[:1000]}  # Limit to first 1000 characters for efficiency

Respond in JSON format:
{{
    "assignment_title": "Assignment Title" or null if no title found,
    "confidence": "high" | "medium" | "low",
    "location": "Description of where the title was found"
}}

If no clear assignment title is found, return null for assignment_title."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content.strip())
        return result
        
    except Exception as e:
        print(f"Error extracting assignment title: {str(e)}")
        return {
            "assignment_title": None,
            "confidence": "low",
            "location": "Error occurred during title extraction"
        }

def extract_text_with_metadata_from_image(image_data, assignment_type=None):
    """
    Enhanced function that extracts text, student name, and assignment title from an image,
    then formats with metadata at the top. Uses multiple extraction methods to ensure reliable
    student name detection, including specialized corner text extraction.
    
    Args:
        image_data (bytes): The image data as bytes
        assignment_type (str, optional): The type of assignment
        
    Returns:
        dict: Contains 'extracted_text', 'student_name_info', 'assignment_title_info', and 'processing_notes'
    """
    try:
        # First extract the text using existing function
        extracted_text = extract_text_from_image(image_data, assignment_type)
        
        # Get specialized corner text extraction - often has student names
        corner_text = extract_corner_text(image_data)
        
        # Then extract student name from the text
        student_name_info = extract_student_name_from_text(extracted_text)
        
        # If no student name found in main text, check corner text
        if not student_name_info.get('student_name'):
            print("No student name found in main text, checking corners...")
            
            # Check top corners first (most common location for student names)
            potential_name = None
            
            if corner_text.get('top_right'):
                top_right = corner_text['top_right']
                # Look for name patterns in top right
                if ":" in top_right:
                    # Might be "Name: John Smith" format
                    parts = top_right.split(":", 1)
                    if len(parts) > 1 and ("name" in parts[0].lower() or "student" in parts[0].lower()):
                        potential_name = parts[1].strip()
                        location = "top right corner (labeled)"
                # If no labeled format, just use the text if it looks like a name (not too long)
                elif len(top_right.split()) <= 4 and len(top_right) < 30:
                    potential_name = top_right.strip()
                    location = "top right corner (unlabeled)"
            
            if not potential_name and corner_text.get('top_left'):
                top_left = corner_text['top_left']
                # Look for name patterns in top left
                if ":" in top_left:
                    # Might be "Name: John Smith" format
                    parts = top_left.split(":", 1)
                    if len(parts) > 1 and ("name" in parts[0].lower() or "student" in parts[0].lower()):
                        potential_name = parts[1].strip()
                        location = "top left corner (labeled)"
                # If no labeled format, just use the text if it looks like a name (not too long)
                elif len(top_left.split()) <= 4 and len(top_left) < 30:
                    potential_name = top_left.strip()
                    location = "top left corner (unlabeled)"
            
            if potential_name:
                print(f"Found potential student name in corner text: {potential_name}")
                student_name_info = {
                    "student_name": potential_name,
                    "confidence": "medium",
                    "location": location
                }
        
        # Extract assignment title from the text
        assignment_title_info = extract_assignment_title_from_text(extracted_text)
        
        # Format the extracted text with metadata at the top
        formatted_text = ""
        
        # Add student name
        if student_name_info and student_name_info.get('student_name'):
            formatted_text = f"**STUDENT: {student_name_info['student_name']}**\n"
        else:
            formatted_text = "**STUDENT: [Name not detected]**\n"
        
        # Add assignment title
        if assignment_title_info and assignment_title_info.get('assignment_title'):
            formatted_text += f"**ASSIGNMENT: {assignment_title_info['assignment_title']}**\n\n"
        else:
            formatted_text += "**ASSIGNMENT: [Title not detected]**\n\n"
        
        formatted_text += "=" * 50 + "\n\n"
        
        # Add the extracted text content
        formatted_text += extracted_text
        
        # Add debug information about student name extraction
        processing_notes = "Text extracted successfully"
        if student_name_info and student_name_info.get('student_name'):
            processing_notes += f". Student name found in {student_name_info.get('location', 'unknown location')}"
        else:
            processing_notes += ". No student name detected"
            
        # Add debug information about corner text extraction
        if corner_text:
            corner_summary = {
                "top_left": corner_text.get('top_left'),
                "top_right": corner_text.get('top_right')
            }
            processing_notes += f". Corner text: {json.dumps(corner_summary)}"
        
        return {
            "extracted_text": formatted_text,
            "student_name_info": student_name_info,
            "assignment_title_info": assignment_title_info,
            "corner_text": corner_text,
            "processing_notes": processing_notes
        }
        
    except Exception as e:
        print(f"Error in enhanced text extraction: {str(e)}")
        return {
            "extracted_text": f"**STUDENT: [Error extracting metadata]**\n\n{'=' * 50}\n\n[Error extracting text: {str(e)}]",
            "student_name_info": {
                "student_name": None,
                "confidence": "low",
                "location": "Error occurred"
            },
            "assignment_title_info": {
                "assignment_title": None,
                "confidence": "low",
                "location": "Error occurred"
            },
            "corner_text": {},
            "processing_notes": f"Error during processing: {str(e)}"
        }

# Keep the old function name as an alias for backward compatibility
def extract_text_and_student_name_from_image(image_data, assignment_type=None):
    """Legacy function maintained for backward compatibility."""
    return extract_text_with_metadata_from_image(image_data, assignment_type)


def analyze_and_grade_mcq_diagrams_first(image_data, assignment_type, rubric):
    """
    Enhanced grading function that prioritizes MCQ and diagram detection/grading
    with special emphasis on MCQ answer matching for full credit.
    """
    try:
        from grader.engine import grade_assignment_with_vision
        from grader import grade_assignment
        
        # Initialize OpenAI client
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Convert image data to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Step 1: Enhanced scan for MCQs with answer detection
        scan_prompt = """Analyze this image comprehensively and detect all content types, with special focus on MCQ answer selections:

**PRIMARY SCAN FOR:**
1. **Multiple Choice Questions (MCQs)** - Questions with A/B/C/D options
   - Look for student selections: bubbled circles, checkmarks, circled letters, highlighted options
   - Identify the selected answer for each MCQ (A, B, C, or D)
   - Note: MCQs should receive full credit if the selected answer is correct, regardless of work shown

2. **Diagram-based questions** - Math graphs, science diagrams, charts, visual problems
3. **Mixed content** - Combination of MCQs, diagrams, and text-based questions
4. **Pure text content** - Essays, short answers, written responses without visual elements

**MCQ ANSWER DETECTION:**
For each MCQ found, specifically identify:
- Question number/identifier
- Available options (A, B, C, D)
- Student's selected answer (look for bubbles, checkmarks, circles, highlighting)
- Confidence level in answer detection

**GRADING STRATEGY DECISION:**
Based on content analysis:
- "vision_primary": If MCQs or diagrams dominate (>50% of content)
- "vision_partial": If MCQs/diagrams are significant (20-50% of content) 
- "ocr_primary": If mostly text-based content (<20% visual elements)

Respond in JSON format:
{
    "strategy": "vision_primary/vision_partial/ocr_primary",
    "mcq_questions": [
        {
            "question_id": "Q1",
            "type": "multiple_choice",
            "location": "top_section",
            "requires_vision": true,
            "student_answer": "B",
            "options": ["A", "B", "C", "D"],
            "answer_confidence": "high",
            "selection_method": "bubbled_circle"
        }
    ],
    "diagram_questions": [
        {
            "question_id": "Q2", 
            "type": "diagram_analysis",
            "location": "middle_section",
            "requires_vision": true,
            "description": "Graph interpretation question"
        }
    ],
    "text_questions": [
        {
            "question_id": "Q3",
            "type": "short_answer",
            "location": "bottom_section",
            "requires_vision": false
        }
    ],
    "confidence": "high/medium/low",
    "total_questions": 3,
    "visual_percentage": 67,
    "mcq_count": 1
}"""
        
        # Call GPT-4 Vision for content analysis
        analysis_response = client.chat.completions.create(
            model=Config.OPENAI_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": scan_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.1
        )
        
        # Parse analysis result
        analysis_content = analysis_response.choices[0].message.content.strip()
        if analysis_content.startswith('```json'):
            analysis_content = analysis_content[7:-3].strip()
        elif analysis_content.startswith('```'):
            analysis_content = analysis_content[3:-3].strip()
            
        analysis = json.loads(analysis_content)
        strategy = analysis.get('strategy', 'ocr_primary')
        mcq_questions = analysis.get('mcq_questions', [])
        
        print(f"Content analysis complete. Strategy: {strategy}")
        print(f"MCQ questions found: {len(mcq_questions)}")
        print(f"Visual content percentage: {analysis.get('visual_percentage', 0)}%")
        
        # Step 2: Execute grading strategy with MCQ emphasis
        if strategy == 'vision_primary':
            # Grade everything with GPT Vision, emphasizing MCQ rules
            print("Using GPT Vision for primary grading (MCQ/diagram dominant)")
            vision_prompt = f"""Grade this assignment using GPT-4 Vision with SPECIAL EMPHASIS on MCQ grading rules.

ASSIGNMENT TYPE: {assignment_type}

RUBRIC:
{rubric}

CONTENT ANALYSIS:
{json.dumps(analysis, indent=2)}

**CRITICAL MCQ GRADING RULES:**
1. **MCQ Full Credit Rule**: For each MCQ, if the student's selected answer matches the correct answer in the rubric, award FULL CREDIT regardless of work shown
2. **Answer Verification**: Compare student selections with correct answers from the rubric
3. **No Work Required**: MCQs do not require showing calculations or explanations
4. **Binary Scoring**: MCQs are either fully correct (full points) or incorrect (zero points)

**DETECTED MCQ ANSWERS:**
{json.dumps(mcq_questions, indent=2)}

**GRADING INSTRUCTIONS:**
1. For each MCQ: Check if student answer matches rubric answer → Award full points if correct
2. For diagrams: Analyze visual content, graphs, charts, mathematical work
3. For text questions: Grade based on content quality and rubric criteria
4. Provide detailed breakdown showing MCQ scoring logic

Respond in JSON format:
{{
    "score": "your_score_here",
    "feedback": "detailed feedback with MCQ analysis",
    "mcq_analysis": "specific breakdown of each MCQ: student answer vs correct answer",
    "diagram_analysis": "analysis of visual elements if applicable",
    "scoring_breakdown": "points awarded for each question type"
}}"""
            
            vision_response = client.chat.completions.create(
                model=Config.OPENAI_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": vision_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            vision_content = vision_response.choices[0].message.content.strip()
            if vision_content.startswith('```json'):
                vision_content = vision_content[7:-3].strip()
            elif vision_content.startswith('```'):
                vision_content = vision_content[3:-3].strip()
                
            result = json.loads(vision_content)
            result['processing_method'] = 'GPT-4 Vision Primary (MCQ-Optimized)'
            result['content_analysis'] = analysis
            
        elif strategy == 'vision_partial':
            # Grade visual elements with Vision (MCQ-optimized), text elements with OCR + Gemini
            print("Using hybrid approach: Vision for MCQ/diagrams, OCR+Gemini for text")
            
            # Grade visual elements first with MCQ emphasis
            visual_questions = analysis.get('mcq_questions', []) + analysis.get('diagram_questions', [])
            if visual_questions:
                vision_prompt = f"""Grade ONLY the MCQ and diagram-based questions in this image with MCQ-optimized scoring.

ASSIGNMENT TYPE: {assignment_type}
RUBRIC: {rubric}

VISUAL QUESTIONS TO GRADE:
{json.dumps(visual_questions, indent=2)}

**MCQ GRADING RULES:**
1. **Full Credit for Correct Answers**: If student MCQ selection matches rubric answer, award full points
2. **No Work Required**: MCQs don't need calculations or explanations
3. **Binary Scoring**: Correct = full points, Incorrect = zero points

**INSTRUCTIONS:**
1. Focus ONLY on MCQ selections and diagram analysis
2. For MCQs: Compare student answers with rubric answers
3. Ignore text-based questions (graded separately)
4. Provide partial score for visual elements only

Respond in JSON format:
{{
    "visual_score": "score for visual elements only",
    "visual_feedback": "feedback for MCQ/diagram questions",
    "mcq_scoring": "detailed MCQ answer analysis",
    "questions_graded": ["list of question IDs graded"]
}}"""
                
                vision_response = client.chat.completions.create(
                    model=Config.OPENAI_VISION_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": vision_prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=1500,
                    temperature=0.3
                )
                
                vision_content = vision_response.choices[0].message.content.strip()
                if vision_content.startswith('```json'):
                    vision_content = vision_content[7:-3].strip()
                elif vision_content.startswith('```'):
                    vision_content = vision_content[3:-3].strip()
                    
                vision_result = json.loads(vision_content)
            else:
                vision_result = {"visual_score": "0", "visual_feedback": "No visual elements found", "questions_graded": []}
            
            # Extract text and grade with Gemini
            extracted_text = extract_text_from_image(image_data, assignment_type)
            text_result = grade_assignment(assignment_type, extracted_text, rubric)
            
            # Combine results
            result = {
                "score": f"Visual: {vision_result['visual_score']}, Text: {text_result['score']}",
                "feedback": f"**MCQ/Visual Elements:** {vision_result['visual_feedback']}\n\n**Text Elements:** {text_result['feedback']}",
                "processing_method": "Hybrid: GPT-4 Vision (MCQ-Optimized) + OCR + Gemini",
                "visual_analysis": vision_result,
                "text_analysis": text_result,
                "extracted_text": extracted_text,
                "content_analysis": analysis
            }
            
        else:  # ocr_primary
            # Standard OCR + Gemini grading
            print("Using standard OCR + Gemini (text-dominant content)")
            extracted_text = extract_text_from_image(image_data, assignment_type)
            result = grade_assignment(assignment_type, extracted_text, rubric)
            result['processing_method'] = 'Standard OCR + Gemini (Text Focus)'
            result['extracted_text'] = extracted_text
            result['content_analysis'] = analysis
        
        return result
        
    except Exception as e:
        print(f"Error in MCQ/diagram-first grading: {str(e)}")
        # Fallback to standard process
        extracted_text = extract_text_from_image(image_data, assignment_type)
        result = grade_assignment(assignment_type, extracted_text, rubric)
        result['processing_method'] = 'Fallback: Standard OCR + Gemini'
        result['extracted_text'] = extracted_text
        result['error'] = str(e)
        return result