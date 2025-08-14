def create_grading_prompt(assignment_type, submission, rubric):
    # Check if this is a math assignment
    if assignment_type.lower() in ['math', 'mathematics', 'calculus', 'algebra', 'geometry', 'statistics', 'problem set']:
        return create_math_grading_prompt(assignment_type, submission, rubric)
    else:
        return create_general_grading_prompt(assignment_type, submission, rubric)

def create_math_grading_prompt(assignment_type, submission_text, rubric):
    prompt = """
    You are an expert mathematics educator grading {assignment_type} assignments with MAXIMUM LENIENCY for OCR-processed work.
    
    **ULTRA-LENIENT GRADING PHILOSOPHY:**
    This submission was processed through OCR and may have significant recognition errors. Your grading must be EXTREMELY FORGIVING.
    
    **FINAL ANSWER PRIORITY SYSTEM:**
    1. **Correct Final Answer = 90-100% credit** (even with minimal/unclear work)
    2. **Correct Final Answer + Any Visible Work = 95-100% credit**
    3. **Correct Final Answer + No Visible Work = 85-95% credit**
    4. **Close/Reasonable Final Answer = 70-90% credit** (assume calculation errors due to OCR)
    5. **Wrong Answer + Correct Method Visible = 60-80% credit**
    6. **Wrong Answer + Some Method Visible = 40-70% credit**
    7. **Some Mathematical Attempt = 25-50% credit**
    
    **OCR ERROR ASSUMPTIONS:**
    - If work appears incomplete, assume student showed more than OCR captured
    - If mathematical notation is unclear, assume student used correct notation
    - If steps seem to jump, assume intermediate steps were present but not captured
    - If final answer is correct, assume the method was largely correct
    
    **GRADING INSTRUCTIONS:**
    1. **FIRST**: Identify all final answers in the submission
    2. **SECOND**: Compare final answers to rubric - if correct, start with high score
    3. **THIRD**: Look for any visible mathematical work or setup
    4. **FOURTH**: Apply OCR leniency - assume more work was shown than visible
    5. **FIFTH**: Award points generously based on final answer correctness
    
    **MULTIPLE CHOICE SPECIAL RULES:**
    - If correct letter appears ANYWHERE in the response, award full credit
    - Don't require work shown for multiple choice questions
    - Any mark near correct letter = full credit
    
    RUBRIC:
    {rubric}
    
    STUDENT SUBMISSION:
    {submission}
    
    **RESPOND WITH MAXIMUM GENEROSITY** in JSON format:
    {{
        "total_score": "earned_points/total_points",
        "percentage": "XX%",
        "questions": [
            {{
                "question_number": 1,
                "points_earned": X,
                "points_possible": Y,
                "student_answer": "[student's final answer]",
                "correct_answer": "[correct answer from rubric]",
                "is_correct": true/false,
                "grading_rationale": "Final answer correct - awarded high score despite OCR limitations",
                "ocr_leniency_applied": true/false,
                "teacher_comment": "Brief comment acknowledging OCR processing"
            }}
        ],
        "overall_feedback": {{
            "strengths": [
                "Correct final answers demonstrate understanding",
                "Mathematical approach appears sound"
            ],
            "areas_for_improvement": [
                "Consider showing more detailed work (note: some work may not have been captured by OCR)"
            ],
            "next_steps": "Continue practicing problem-solving methods"
        }},
        "grading_notes": "OCR processing applied - grading focused on final answer accuracy with maximum leniency for unclear work"
    }}
    """.format(assignment_type=assignment_type, rubric=rubric, submission=submission_text)
    
    return prompt

def create_general_grading_prompt(assignment_type, submission, rubric):
    prompt = """
    You are an expert educator with years of experience grading {assignment_type} assignments.
    
    **CRITICAL OCR TOLERANCE INSTRUCTIONS:**
    This submission was processed through OCR and may contain errors. Be EXTREMELY LENIENT with:
    - Unclear or garbled text
    - Missing formatting
    - Misinterpreted symbols or characters
    - Incomplete sentences due to OCR limitations
    
    ENHANCED GRADING PHILOSOPHY:
    - Prioritize content understanding over perfect presentation
    - Give benefit of doubt when text seems incomplete due to OCR
    - Look for key concepts and ideas even if poorly formatted
    - Be generous with partial credit when main ideas are present
    
    RUBRIC:
    {rubric}
    
    STUDENT SUBMISSION:
    {submission}
    
    **TEACHER-FRIENDLY OUTPUT FORMAT:**
    Provide detailed, actionable feedback that teachers can use immediately.
    
    Respond in JSON format with this EXACT structure:
    {{
        "total_score": "earned_points/total_points",
        "percentage": "XX%",
        "questions": [
            {{
                "question_number": 1,
                "points_earned": X,
                "points_possible": Y,
                "student_response": "[key parts of student's response]",
                "expected_response": "[what was expected based on rubric]",
                "is_satisfactory": true/false,
                "mistakes_identified": [
                    "Specific issue 1",
                    "Specific issue 2"
                ],
                "partial_credit_given_for": [
                    "Correct concept understanding",
                    "Good examples provided"
                ],
                "teacher_comment": "Brief comment for teacher records"
            }}
        ],
        "overall_feedback": {{
            "strengths": [
                "Specific strength 1",
                "Specific strength 2"
            ],
            "areas_for_improvement": [
                "Specific area 1 with actionable advice",
                "Specific area 2 with actionable advice"
            ],
            "next_steps": "Specific recommendations for student improvement"
        }},
        "grading_notes": "Any OCR-related considerations or grading decisions for teacher reference"
    }}
    """.format(assignment_type=assignment_type, rubric=rubric, submission=submission)
    
    # Add OCR-tolerant multiple choice handling
    if assignment_type and assignment_type.lower() in ['multiple choice', 'problem set']:
        mc_instructions = """
        
**MULTIPLE CHOICE + OCR GRADING INSTRUCTIONS:**
- For multiple choice questions, include "question_type": "multiple_choice" in the question object
- Add "student_selection" and "all_choices" fields
- **IMPORTANT**: Multiple choice questions do NOT require work shown
- **OCR TOLERANCE**: Give benefit of doubt when selections are unclear
        """
        
        prompt += mc_instructions
    
    return prompt