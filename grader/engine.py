import json
from openai import OpenAI
from config import Config
from grader.prompts import create_grading_prompt
from grader.gemini_engine import grade_assignment_with_gemini

def grade_assignment_with_vision(assignment_type, image_data, rubric, diagram_info=None, student_name=None):
    """
    Grades assignments with diagrams using GPT-4 Vision for direct visual analysis.
    
    Args:
        assignment_type (str): The type of assignment
        image_data (bytes): The image data containing diagrams
        rubric (str): The grading rubric
        diagram_info (dict): Information about detected diagrams
        
    Returns:
        dict: A dictionary containing the score and feedback
    """
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Convert image data to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Create specialized prompt for diagram grading
        diagram_context = ""
        if diagram_info and diagram_info.get('has_diagrams'):
            diagram_types = ", ".join(diagram_info.get('diagram_types', []))
            diagram_context = f"\n\nNOTE: This submission contains visual elements including: {diagram_types}. Please analyze both the visual content and any text when grading."
        
        # Enhanced prompt with MCQ-specific instructions
        prompt = f"""You are an expert grader specializing in assignments that contain visual elements like diagrams, charts, illustrations, and Multiple Choice Questions (MCQs).

ASSIGNMENT TYPE: {assignment_type}

RUBRIC:
{rubric}{diagram_context}

**CRITICAL MCQ GRADING RULES:**
1. **For Multiple Choice Questions**: If the student's selected answer matches the correct answer according to the rubric, award FULL CREDIT for that question regardless of whether work is shown
2. **Answer Detection**: Look for bubbled circles, checkmarks, circled letters, or any clear indication of student selection (A, B, C, D, etc.)
3. **No Work Required**: MCQs do not require showing work - only the correct final answer selection matters
4. **Partial Credit**: Only deduct points if the selected answer is incorrect, not for lack of work shown

**GENERAL GRADING INSTRUCTIONS:**
1. Carefully examine the entire image, paying special attention to:
   - Multiple Choice answer selections (bubbles, checkmarks, circled options)
   - Diagrams, charts, graphs, and visual representations
   - Mathematical work, equations, and calculations
   - Text content and written explanations
   - Connections between visual and textual elements

2. Analyze the rubric to determine the total possible points
3. For MCQs: Award full points if correct answer is selected, zero if incorrect
4. For other questions: Grade according to rubric criteria, considering both visual and textual content
5. If the rubric specifies a total other than 100 points, output the score as a fraction (e.g., "8/10")
6. If the rubric uses a 0-100 scale or doesn't specify, output a numeric score (0-100)
7. Provide detailed feedback that addresses both visual and textual elements

Please respond in JSON format:
{{
    "score": "your_score_here",
    "feedback": "detailed feedback explaining the grade, including analysis of visual elements and MCQ selections",
    "mcq_breakdown": "specific analysis of each MCQ answer if applicable"
}}"""
        
        # Call GPT-4 Vision
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
            max_tokens=2000,
            temperature=0.3
        )
        
        # Extract and parse the response
        content = response.choices[0].message.content.strip()
        
        # Clean JSON response if needed
        if content.startswith('```json'):
            content = content[7:-3].strip()
        elif content.startswith('```'):
            content = content[3:-3].strip()
            
        result = json.loads(content)
        
        # Validate the result structure
        if 'score' not in result or 'feedback' not in result:
            raise ValueError("Response missing required fields")
            
        return {
            "score": result['score'],
            "feedback": result['feedback'],
            "grading_method": "GPT-4 Vision (Diagram Analysis)"
        }
        
    except Exception as e:
        print(f"Error in GPT-4 Vision grading: {str(e)}")
        raise Exception(f"Error during vision-based grading: {str(e)}")

def grade_assignment(assignment_type, submission, rubric, student_name=None, assignment_title=None):
    """
    Grades an assignment using Google Gemini model based on the provided rubric.
    
    Args:
        assignment_type (str): The type of assignment
        submission (str): The text submission to grade
        rubric (str): The grading rubric
        student_name (str, optional): The name of the student
        assignment_title (str, optional): The title of the assignment
    This function now routes to Gemini instead of GPT-4 for grading.
    
    Args:
        assignment_type (str): The type of assignment (e.g., Essay, Multiple Choice, etc.)
        submission (str): The student's submission to be graded
        rubric (str): The grading rubric to be used for evaluation
        
    Returns:
        dict: A dictionary containing the score and feedback
    """
    # Route to Gemini for grading with metadata
    return grade_assignment_with_gemini(assignment_type, submission, rubric, student_name, assignment_title)

# Keep the original GPT-4 function for fallback if needed
def grade_assignment_with_gpt4(assignment_type, submission, rubric):
    """
    Original GPT-4 grading function - kept for fallback purposes.
    """
    # Initialize OpenAI client
    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    # Create the prompt for the GPT-4 model
    prompt = create_grading_prompt(assignment_type, submission, rubric)
    
    try:
        # Debug: Print the model being used
        print(f"Using OpenAI model: {Config.OPENAI_MODEL}")
        print(f"API Key present: {bool(Config.OPENAI_API_KEY)}")
        
        # Call the OpenAI API with timeout
        response = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert grading assistant that evaluates student work based on provided rubrics."},
                {"role": "user", "content": prompt}
            ],
            # temperature=0.3,  # GPT-5 models only support default temperature of 1
            max_completion_tokens=4000,  # Increased from 2000 to 4000
            timeout=30  # Add 30 second timeout
        )
        # Around line 40-50, add more debugging
        print(f"OpenAI API call successful. Response received.")
        print(f"Full response object: {response}")
        print(f"Response choices: {response.choices}")
        print(f"Message content: {response.choices[0].message.content}")
        
        # Extract the response content
        content = response.choices[0].message.content
        print(f"Raw content before processing: '{content}'")
        
        if content is None:
            print("ERROR: Content is None!")
            content = ""
        else:
            content = content.strip()
        
        # Debug: Print the raw response
        print(f"Raw GPT response: {content}")
        
        # Clean the response - remove markdown code blocks if present
        if content.startswith('```json'):
            # Remove ```json from start and ``` from end
            content = content[7:]  # Remove '```json'
            if content.endswith('```'):
                content = content[:-3]  # Remove '```'
            content = content.strip()
        elif content.startswith('```'):
            # Remove generic ``` blocks
            content = content[3:]  # Remove '```'
            if content.endswith('```'):
                content = content[:-3]  # Remove '```'
            content = content.strip()
        
        print(f"Cleaned content for parsing: {content}")
        
        # Parse the JSON response
        try:
            result = json.loads(content)
            
            # Validate the result structure
            if 'score' not in result or 'feedback' not in result:
                raise ValueError("Response missing required fields")
                
            # Handle both numeric and fractional scores
            score_value = result['score']
            
            # If score is a string (fractional format), keep it as is
            if isinstance(score_value, str):
                # Validate fractional format (e.g., "7/10")
                if '/' in score_value:
                    try:
                        parts = score_value.split('/')
                        if len(parts) == 2:
                            earned = float(parts[0])
                            total = float(parts[1])
                            if earned < 0 or earned > total or total <= 0:
                                raise ValueError("Invalid fractional score format")
                        else:
                            raise ValueError("Invalid fractional score format")
                    except (ValueError, IndexError):
                        raise ValueError("Invalid fractional score format")
                else:
                    # Try to convert string to numeric
                    try:
                        score_value = float(score_value)
                        if score_value < 0 or score_value > 100:
                            raise ValueError("Score must be between 0 and 100")
                    except ValueError:
                        raise ValueError("Invalid score format")
            else:
                # Numeric score validation
                score_value = float(score_value)
                if score_value < 0 or score_value > 100:
                    raise ValueError("Score must be between 0 and 100")
                
            return {
                "score": score_value,
                "feedback": result['feedback']
            }
            
        except json.JSONDecodeError:
            raise ValueError("Failed to parse GPT-4 response as JSON")
            
    except Exception as e:
        # Enhanced error logging
        print(f"Error during grading: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        # Return error information instead of raising exception
        return {
            "score": "Error",
            "feedback": f"""**GRADING ERROR**\n\nAn error occurred during grading: {str(e)}
            
Please try again. If the issue persists, contact support."""
        }