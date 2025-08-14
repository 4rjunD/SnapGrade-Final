#!/usr/bin/env python3
"""
GPT Model Training Script for SnapGrade

This script helps you train a custom GPT model on your grading data.

Usage:
    python3 train_model.py --dataset /path/to/your/dataset
    
Dataset Format:
    Your dataset folder should contain JSON or CSV files with the following structure:
    
    JSON format:
    [
        {
            "submission": "Student's answer text",
            "rubric": "Grading rubric text", 
            "score": "8/10" or "85",
            "feedback": "Detailed feedback text"
        },
        ...
    ]
    
    CSV format:
    submission,rubric,score,feedback
    "Student answer","Rubric text","8/10","Feedback text"
    ...
"""

import argparse
import os
import sys
from grader.fine_tuning import train_model_on_dataset, GPTFineTuner

def main():
    parser = argparse.ArgumentParser(
        description='Train a custom GPT model on your grading data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--dataset', 
        required=True,
        help='Path to your dataset folder containing JSON/CSV files'
    )
    
    parser.add_argument(
        '--model',
        default='gpt-3.5-turbo',
        choices=['gpt-3.5-turbo', 'gpt-4'],
        help='Base model to fine-tune (default: gpt-3.5-turbo)'
    )
    
    parser.add_argument(
        '--suffix',
        help='Optional suffix for the fine-tuned model name'
    )
    
    parser.add_argument(
        '--no-wait',
        action='store_true',
        help='Don\'t wait for training to complete (just start the job)'
    )
    
    parser.add_argument(
        '--check-status',
        help='Check status of an existing fine-tuning job by job ID'
    )
    
    args = parser.parse_args()
    
    # Check if we're just checking status
    if args.check_status:
        fine_tuner = GPTFineTuner()
        try:
            status_info = fine_tuner.check_job_status(args.check_status)
            print("\n=== Job Status ===")
            for key, value in status_info.items():
                print(f"{key}: {value}")
            return
        except Exception as e:
            print(f"Error checking job status: {e}")
            sys.exit(1)
    
    # Validate dataset path
    if not os.path.exists(args.dataset):
        print(f"Error: Dataset folder not found: {args.dataset}")
        sys.exit(1)
    
    if not os.path.isdir(args.dataset):
        print(f"Error: Dataset path is not a directory: {args.dataset}")
        sys.exit(1)
    
    # Check for data files
    data_files = [f for f in os.listdir(args.dataset) if f.endswith(('.json', '.csv'))]
    if not data_files:
        print(f"Error: No JSON or CSV files found in dataset folder: {args.dataset}")
        print("Please ensure your dataset folder contains files with grading data.")
        sys.exit(1)
    
    print(f"Found {len(data_files)} data files: {', '.join(data_files)}")
    
    # Confirm before starting
    print(f"\n=== Training Configuration ===")
    print(f"Dataset folder: {args.dataset}")
    print(f"Base model: {args.model}")
    print(f"Model suffix: {args.suffix or 'None'}")
    print(f"Wait for completion: {not args.no_wait}")
    
    confirm = input("\nProceed with training? (y/N): ")
    if confirm.lower() != 'y':
        print("Training cancelled.")
        return
    
    try:
        print("\n=== Starting Training Process ===")
        result = train_model_on_dataset(
            dataset_folder_path=args.dataset,
            model=args.model,
            suffix=args.suffix,
            wait_for_completion=not args.no_wait
        )
        
        print("\n=== Training Results ===")
        print(f"Job ID: {result['job_id']}")
        print(f"File ID: {result['file_id']}")
        print(f"Training file: {result['training_file_path']}")
        print(f"Status: {result['status']}")
        
        if 'fine_tuned_model_id' in result:
            print(f"Fine-tuned model: {result['fine_tuned_model_id']}")
            print("\n=== Next Steps ===")
            print(f"1. Update your .env file with: OPENAI_MODEL={result['fine_tuned_model_id']}")
            print("2. Restart your SnapGrade server to use the new model")
        else:
            print("\n=== Next Steps ===")
            print(f"1. Check training status with: python3 train_model.py --check-status {result['job_id']}")
            print("2. Training typically takes 10-30 minutes depending on dataset size")
            print("3. Once completed, update your .env file with the new model ID")
        
    except Exception as e:
        print(f"\nError during training: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()