import json
import re
import google.generativeai as genai
from config import Config
from grader.prompts import create_grading_prompt

# Configure Gemini API
genai.configure(api_key=Config.GEMINI_API_KEY)

def preprocess_submission_for_ocr_errors(submission, assignment_type):
    """
    Preprocesses submission text to handle common OCR errors,
    with enhanced leniency for final answer recognition.
    """
    if assignment_type.lower() in ['math', 'mathematics', 'calculus', 'algebra', 'geometry', 'statistics', 'problem set']:
        # Create a comprehensive note about OCR leniency
        ocr_note = """\n\n[CRITICAL GRADING NOTE: This submission was processed through OCR and may have significant text recognition errors. 
APPLY MAXIMUM LENIENCY:
- If final answers are correct, award 85-100% credit regardless of work clarity
- Common OCR errors: 5↔S, 0↔O, 1↔l↔I, 6↔G, 8↔B, 2↔Z, +↔t, ×↔x
- Assume student showed more work than OCR captured
- Focus on mathematical reasoning that can be inferred from visible elements
- Give benefit of doubt when work seems incomplete due to OCR limitations]\n\n"""
        return ocr_note + submission
    return submission

def extract_final_answers(submission):
    """
    Enhanced final answer extraction with more aggressive pattern matching.
    """
    # Enhanced patterns for final answer detection
    patterns = [
        r'(?:answer|final|result|solution)\s*[:=]?\s*([^\n]+)',  # "Answer: 42"
        r'(?:^|\n)\s*([0-9]+(?:\.[0-9]+)?(?:\s*[a-zA-Z]*)?\s*)(?=\s*$|\n)',  # Numbers at end of lines
        r'(?:^|\n)\s*([A-D])\s*(?=\s*$|\n)',  # Multiple choice letters
        r'(?:^|\n)\s*([0-9]+(?:\.[0-9]+)?\s*[+\-*/]?\s*[0-9]*(?:\.[0-9]+)?\s*)(?=\s*$|\n)',  # Math expressions
        r'\[([^\]]+)\]',  # Anything in brackets (often final answers)
        r'=\s*([0-9]+(?:\.[0-9]+)?)',  # Equals followed by number
    ]
    
    potential_answers = []
    for pattern in patterns:
        matches = re.findall(pattern, submission, re.IGNORECASE | re.MULTILINE)
        potential_answers.extend(matches)
    
    if potential_answers:
        # Remove duplicates and clean up
        unique_answers = list(set([ans.strip() for ans in potential_answers if ans.strip()]))
        answer_note = f"\n\n[DETECTED FINAL ANSWERS - PRIORITIZE THESE: {', '.join(unique_answers)}]\n\n"
        return answer_note
    return ""

# Add MCQ-specific instructions to the Gemini grading prompt
# This ensures consistency when MCQs are processed through OCR

def grade_assignment_with_gemini(assignment_type, submission, rubric, student_name=None, assignment_title=None):
    """
    Enhanced Gemini grading with student name and assignment title in feedback header
    
    Args:
        assignment_type (str): The type of assignment
        submission (str): The text submission to grade
        rubric (str): The rubric to use for grading
        student_name (str, optional): The name of the student
        assignment_title (str, optional): The title of the assignment
        
    Returns:
        dict: Contains grading results including score and feedback
    """
    try:
        # Preprocess submission for OCR error handling
        processed_submission = preprocess_submission_for_ocr_errors(submission, assignment_type)
        
        # Add final answer extraction for math assignments
        if assignment_type.lower() in ['math', 'mathematics', 'calculus', 'algebra', 'geometry', 'statistics', 'problem set']:
            answer_hints = extract_final_answers(submission)
            processed_submission += answer_hints
        
        # Extract student name from submission if not provided
        if not student_name:
            # Look for student name in the submission text
            import re
            name_patterns = [
                r'\*\*STUDENT:\s*([^\*\n]+)\*\*',  # **STUDENT: Name**
                r'Name:\s*([^\n]+)',
                r'Student:\s*([^\n]+)',
                r'By:\s*([^\n]+)'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, processed_submission, re.IGNORECASE)
                if match:
                    student_name = match.group(1).strip()
                    if student_name and student_name != "[Name not detected]" and student_name != "[Error extracting name]":
                        break
        
        # Add OCR leniency note for all math-related assignments
        if assignment_type.lower() in ['math', 'mathematics', 'calculus', 'algebra', 'geometry', 'statistics', 'problem set']:
            ocr_leniency_note = "\n\n[GRADING INSTRUCTION: Apply maximum leniency. If final answers are correct, award high scores regardless of work clarity. Assume OCR missed some student work.]\n\n"
            processed_submission += ocr_leniency_note
        
        # Initialize Gemini model - try different approaches for compatibility
        try:
            # Try the newer API first
            model = genai.GenerativeModel(Config.GEMINI_MODEL)
        except AttributeError:
            # Fallback for older versions
            model = genai.GenerativeModel(model_name=Config.GEMINI_MODEL)
        
        # Create the prompt for the Gemini model (reusing existing prompt structure)
        prompt = create_grading_prompt(assignment_type, processed_submission, rubric)
        
        # Debug: Print the model being used
        print(f"Using Gemini model: {Config.GEMINI_MODEL}")
        print(f"Gemini API Key present: {bool(Config.GEMINI_API_KEY)}")
        print(f"OCR preprocessing applied: {assignment_type.lower() in ['math', 'mathematics', 'calculus', 'algebra', 'geometry', 'statistics', 'problem set']}")
        
        # Configure generation parameters specifically for math grading
        if assignment_type.lower() in ['math', 'mathematics', 'calculus', 'algebra', 'geometry', 'statistics', 'problem set']:
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,  # Even lower temperature for more consistent math grading with OCR tolerance
                top_p=0.95,  # Higher top_p for more comprehensive consideration
                top_k=30,
                max_output_tokens=5000,  # More tokens for detailed question-by-question feedback
            )
            print("Using math-optimized grading parameters with OCR tolerance")
        else:
            generation_config = genai.types.GenerationConfig(
                temperature=0.3,
                top_p=0.8,
                top_k=40,
                max_output_tokens=4000,
            )
        
        # Call the Gemini API
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        print(f"Gemini API call successful. Response received.")
        
        # Extract the response content
        content = response.text
        print(f"Raw content before processing: '{content}'")
        
        if content is None:
            print("ERROR: Content is None!")
            content = ""
        else:
            content = content.strip()
        
        # Debug: Print the raw response
        print(f"Raw Gemini response: {content}")
        
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
            # Fix common escape sequence issues before parsing
            # Replace invalid escape sequences that might break JSON parsing
            sanitized_content = content
            
            # Look for escaped backslashes that aren't valid JSON escape sequences
            import re
            # Fix common invalid escape sequences
            sanitized_content = re.sub(r'\\([^"\\/bfnrtu])', r'\\\\\1', sanitized_content)
            
            # Additional safety measure: replace any remaining problematic backslashes
            sanitized_content = sanitized_content.replace('\\', '\\\\')
            # But preserve valid JSON escape sequences
            for valid_escape in ['\\"', '\\/', '\\b', '\\f', '\\n', '\\r', '\\t']:
                sanitized_content = sanitized_content.replace('\\\\' + valid_escape[1:], valid_escape)
            
            print(f"Sanitized content for parsing: {sanitized_content[:100]}...")
            
            try:
                # Try to parse the sanitized content
                result = json.loads(sanitized_content)
            except json.JSONDecodeError:
                # If that fails, try with a more aggressive approach: replace all backslashes
                print("First JSON parsing attempt failed, trying with additional sanitization")
                # Manual JSON object construction as a fallback
                if '{' in content and '}' in content:
                    # Extract the content between curly braces
                    content_between_braces = content[content.find('{')+1:content.rfind('}')]
                    # Split by commas and construct a simple JSON structure
                    pairs = content_between_braces.split(',')
                    result = {}
                    for pair in pairs:
                        if ':' in pair:
                            key, value = pair.split(':', 1)
                            # Clean up key and value
                            key = key.strip().strip('"\'')
                            value = value.strip().strip('"\'')
                            result[key] = value
                    
                    # Default values if missing
                    if 'score' not in result and 'total_score' not in result:
                        result['score'] = "N/A"
                    if 'feedback' not in result:
                        result['feedback'] = "Error parsing the grading response. Please try again."
                else:
                    # If all parsing fails, create a generic response
                    result = {
                        "score": "N/A",
                        "feedback": f"Unable to parse grading result. Raw response: {content[:500]}..."
                    }
            
            # Handle new detailed JSON structure
            if 'total_score' in result:
                # New detailed format
                score_value = result['total_score']
                
                # Create comprehensive feedback with student name header
                feedback_parts = []
                
                # Add student name and assignment title header
                if student_name and student_name.strip():
                    feedback_parts.append(f"**STUDENT: {student_name.upper()}**")
                    
                    if assignment_title and assignment_title.strip():
                        feedback_parts.append(f"**ASSIGNMENT: {assignment_title}**")
                    
                    feedback_parts.append("=" * 60)
                else:
                    if assignment_title and assignment_title.strip():
                        feedback_parts.append(f"**ASSIGNMENT: {assignment_title}**")
                        feedback_parts.append("=" * 30)
                    else:
                        feedback_parts.append("**GRADING REPORT**")
                        feedback_parts.append("=" * 30)
                
                # Add overall summary
                if 'percentage' in result:
                    feedback_parts.append(f"\n**Overall Score: {result['percentage']}**")
                
                # Add question-by-question breakdown
                if 'questions' in result and result['questions']:
                    feedback_parts.append("\n**Question-by-Question Analysis:**")
                    for q in result['questions']:
                        q_feedback = f"\nQuestion {q.get('question_number', '?')}: {q.get('points_earned', 0)}/{q.get('points_possible', 0)} points"
                        if q.get('mistakes_identified'):
                            q_feedback += f"\n- Issues: {', '.join(q['mistakes_identified'])}"
                        if q.get('partial_credit_given_for'):
                            q_feedback += f"\n- Credit given for: {', '.join(q['partial_credit_given_for'])}"
                        if q.get('teacher_comment'):
                            q_feedback += f"\n- Note: {q['teacher_comment']}"
                        feedback_parts.append(q_feedback)
                
                # Add overall feedback
                if 'overall_feedback' in result:
                    of = result['overall_feedback']
                    if of.get('strengths'):
                        feedback_parts.append(f"\n**Strengths:**\n- {chr(10).join(of['strengths'])}")
                    if of.get('areas_for_improvement'):
                        feedback_parts.append(f"\n**Areas for Improvement:**\n- {chr(10).join(of['areas_for_improvement'])}")
                    if of.get('next_steps'):
                        feedback_parts.append(f"\n**Next Steps:** {of['next_steps']}")
                
                # Add grading notes if present
                if 'grading_notes' in result:
                    feedback_parts.append(f"\n**Grading Notes:** {result['grading_notes']}")
                
                feedback_value = "\n".join(feedback_parts)
                
            elif 'score' in result and 'feedback' in result:
                # Legacy format - add student name and assignment title header
                score_value = result['score']
                
                if student_name and student_name.strip():
                    if assignment_title and assignment_title.strip():
                        feedback_value = f"**STUDENT: {student_name.upper()}**\n**ASSIGNMENT: {assignment_title}**\n{'=' * 60}\n\n{result['feedback']}"
                    else:
                        feedback_value = f"**STUDENT: {student_name.upper()}**\n{'=' * 60}\n\n{result['feedback']}"
                else:
                    if assignment_title and assignment_title.strip():
                        feedback_value = f"**ASSIGNMENT: {assignment_title}**\n{'=' * 30}\n\n{result['feedback']}"
                    else:
                        feedback_value = f"**GRADING REPORT**\n{'=' * 30}\n\n{result['feedback']}"
            else:
                raise ValueError("Response missing required fields (expected 'total_score' or 'score'/'feedback')")
                
            # REMOVE THE OLD VALIDATION - it's redundant now
            # The validation logic should continue from here with score_value and feedback_value
            
            # Handle both numeric and fractional scores (same logic as original)
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
                
            # Enhanced math score validation with OCR bonus
            if isinstance(score_value, str) and '/' in score_value:
                parts = score_value.split('/')
                earned = float(parts[0])
                total = float(parts[1])
                
                # Math-specific OCR leniency bonus
                if assignment_type.lower() in ['math', 'mathematics', 'calculus', 'algebra', 'geometry', 'statistics', 'problem set']:
                    # Round to nearest whole number for math assignments
                    earned = round(earned)
                    
                    # Apply generous OCR-friendly bonus
                    if earned >= total * 0.85 and earned < total:  # Lowered threshold from 0.95 to 0.85
                        print(f"OCR leniency bonus applied: rounding {earned}/{total} up to {total}/{total}")
                        earned = total
                    elif earned >= total * 0.75 and earned < total * 0.85:  # Additional tier
                        bonus_points = min(2, total - earned)  # Add up to 2 bonus points
                        earned += bonus_points
                        print(f"OCR partial bonus applied: added {bonus_points} points")
                    
                    score_value = f"{earned}/{total}"
                    print(f"Math assignment score with OCR leniency: {score_value}")
            
            # For structured JSON format, return both a formatted feedback string AND the original structured object
            if 'total_score' in result:
                return {
                    "score": score_value,
                    "feedback": result,  # Return the entire structured JSON object
                    "formatted_feedback": feedback_value  # Add formatted string version
                }
            else:
                return {
                    "score": score_value,
                    "feedback": feedback_value
                }
            
        except json.JSONDecodeError as json_err:
            print(f"JSON parsing error: {str(json_err)}")
            print(f"Problematic content: {content[:200]}...")
            
            # Create a fallback response
            return {
                "score": "N/A",
                "feedback": f"""**GRADING ERROR**\n\nWe encountered an issue while processing the grading response. 
                
Here is what we could extract:\n\n{content[:1000]}...\n\n
Please try submitting again. If the issue persists, try uploading a clearer image or providing more text context."""
            }
            
    except Exception as e:
        # Enhanced error logging
        print(f"Error during Gemini grading: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        # Return a user-friendly error message instead of raising an exception
        return {
            "score": "Error",
            "feedback": f"""**GRADING ERROR**\n\nWe encountered an issue while processing your submission: {str(e)}
            
Please try submitting again. If the issue persists, you might try:
1. Uploading a clearer image
2. Providing more context in your submission
3. Using a different file format
4. Selecting a different assignment type

Technical Details: {type(e).__name__}"""
        }