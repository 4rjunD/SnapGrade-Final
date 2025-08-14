#!/usr/bin/env python3
"""
Script to generate training data from the mathematics dataset for GPT fine-tuning.
This script generates math problems and formats them for SnapGrade training.
"""

import json
import os
import sys
import argparse
from typing import List, Dict, Any

# Add the mathematics_dataset to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dataset', 'mathematics_dataset-master'))

try:
    # Import required modules
    from mathematics_dataset.modules import modules
    from mathematics_dataset import example
    from mathematics_dataset import generate_settings
except ImportError as e:
    print(f"Error importing mathematics_dataset: {e}")
    print("Please ensure the mathematics_dataset is properly installed.")
    sys.exit(1)


def _make_entropy_fn(level, num_levels):
    """Create entropy function for difficulty levels."""
    lower = level / num_levels
    upper = (level + 1) / num_levels
    def modify_entropy(range_):
        assert len(range_) == 2
        length = range_[1] - range_[0]
        return (range_[0] + lower * length, range_[0] + upper * length)
    return modify_entropy


def sample_from_module(module):
    """Sample a problem from a module, checking length constraints."""
    num_dropped = 0
    while True:
        problem = module()
        question = str(problem.question)
        if len(question) > generate_settings.MAX_QUESTION_LENGTH:
            num_dropped += 1
            if num_dropped > 10:  # Avoid infinite loop
                break
            continue
        answer = str(problem.answer)
        if len(answer) > generate_settings.MAX_ANSWER_LENGTH:
            num_dropped += 1
            if num_dropped > 10:  # Avoid infinite loop
                break
            continue
        return problem, num_dropped
    return None, num_dropped


def get_modules_for_difficulty(difficulty: str):
    """Get modules for the specified difficulty level."""
    if difficulty == 'easy':
        entropy_fn = _make_entropy_fn(0, 3)
    elif difficulty == 'medium':
        entropy_fn = _make_entropy_fn(1, 3)
    elif difficulty == 'hard':
        entropy_fn = _make_entropy_fn(2, 3)
    else:
        entropy_fn = _make_entropy_fn(1, 3)  # Default to medium
    
    return modules.train(entropy_fn)


def flatten_modules(modules_dict, prefix=None):
    """Flatten nested module dictionary."""
    flat = {}
    for key, module_or_function in modules_dict.items():
        full_name = prefix + '__' + key if prefix is not None else key
        if isinstance(module_or_function, dict):
            flat.update(flatten_modules(module_or_function, full_name))
        else:
            flat[full_name] = module_or_function
    return flat


def generate_math_problems(num_problems: int = 1000, difficulty: str = 'medium') -> List[Dict[str, Any]]:
    """
    Generate math problems from the mathematics dataset.
    
    Args:
        num_problems: Number of problems to generate
        difficulty: Difficulty level ('easy', 'medium', 'hard')
    
    Returns:
        List of training examples in the format needed for GPT fine-tuning
    """
    training_data = []
    
    print(f"Getting modules for difficulty: {difficulty}")
    modules_dict = get_modules_for_difficulty(difficulty)
    flat_modules = flatten_modules(modules_dict)
    
    print(f"Found {len(flat_modules)} modules")
    print(f"Generating {num_problems} problems...")
    
    problems_per_module = max(1, num_problems // len(flat_modules))
    generated_count = 0
    
    for module_name, module in flat_modules.items():
        if generated_count >= num_problems:
            break
            
        print(f"Generating from module: {module_name}")
        
        for i in range(problems_per_module):
            if generated_count >= num_problems:
                break
                
            try:
                result = sample_from_module(module)
                if result[0] is None:
                    print(f"Skipping module {module_name} - too many dropped problems")
                    break
                    
                problem, num_dropped = result
                
                # Create a rubric based on the module type
                rubric = create_rubric_for_module(module_name)
                
                # Create training example
                training_example = {
                    "submission": str(problem.question),
                    "rubric": rubric,
                    "score": "10/10",  # Assuming correct answers get full score
                    "feedback": f"Correct answer: {problem.answer}. This demonstrates proper understanding of {module_name.replace('__', ' ').replace('_', ' ')}."
                }
                
                training_data.append(training_example)
                generated_count += 1
                
                if generated_count % 50 == 0:
                    print(f"Generated {generated_count} problems...")
                    
            except Exception as e:
                print(f"Error generating problem from {module_name}: {e}")
                continue
    
    print(f"Successfully generated {len(training_data)} training examples")
    return training_data


def create_rubric_for_module(module_name: str) -> str:
    """
    Create a rubric based on the mathematics module type.
    
    Args:
        module_name: Name of the mathematics module
    
    Returns:
        Appropriate rubric string
    """
    rubrics = {
        'algebra': "Solve algebraic equations correctly (10 points): Show proper algebraic manipulation and arrive at the correct solution.",
        'arithmetic': "Perform arithmetic calculations accurately (10 points): Execute all operations correctly and provide the exact numerical result.",
        'calculus': "Apply calculus concepts correctly (10 points): Use proper differentiation/integration techniques and show mathematical reasoning.",
        'comparison': "Make accurate comparisons (10 points): Correctly identify relationships between numbers or expressions.",
        'measurement': "Handle units and measurements properly (10 points): Convert units correctly and work with time/measurement concepts.",
        'numbers': "Demonstrate number theory understanding (10 points): Work with prime numbers, divisors, base conversion, and number properties.",
        'polynomials': "Manipulate polynomials correctly (10 points): Perform polynomial operations, simplification, and evaluation accurately.",
        'probability': "Calculate probabilities correctly (10 points): Apply probability concepts and provide accurate probability values."
    }
    
    # Find the best matching rubric
    for key, rubric in rubrics.items():
        if key in module_name.lower():
            return rubric
    
    # Default rubric
    return "Solve the mathematical problem correctly (10 points): Show proper mathematical reasoning and arrive at the correct answer."


def save_training_data(training_data: List[Dict[str, Any]], output_file: str):
    """
    Save training data to a JSON file.
    
    Args:
        training_data: List of training examples
        output_file: Path to output file
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, indent=2, ensure_ascii=False)
    
    print(f"Training data saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Generate training data from mathematics dataset')
    parser.add_argument('--num_problems', type=int, default=1000, 
                       help='Number of problems to generate (default: 1000)')
    parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard'], default='medium',
                       help='Difficulty level (default: medium)')
    parser.add_argument('--output', type=str, default='./dataset/math_training_data.json',
                       help='Output file path (default: ./dataset/math_training_data.json)')
    
    args = parser.parse_args()
    
    print(f"Generating {args.num_problems} {args.difficulty} math problems...")
    
    try:
        training_data = generate_math_problems(args.num_problems, args.difficulty)
        save_training_data(training_data, args.output)
        
        print(f"\nTraining data generation complete!")
        print(f"Generated {len(training_data)} examples")
        print(f"Saved to: {args.output}")
        print(f"\nTo train your model, run:")
        print(f"python3 train_model.py --dataset {args.output}")
        
    except Exception as e:
        print(f"Error generating training data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()