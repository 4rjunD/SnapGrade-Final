import json
import os
from openai import OpenAI
from config import Config
from datetime import datetime
import time

class GPTFineTuner:
    """
    Class to handle GPT model fine-tuning using OpenAI's API.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.training_data_folder = os.path.join(os.path.dirname(__file__), '..', 'training_data')
        os.makedirs(self.training_data_folder, exist_ok=True)
    
    def prepare_training_data(self, dataset_folder_path):
        """
        Prepare training data from your dataset folder.
        
        Args:
            dataset_folder_path (str): Path to your dataset folder
            
        Returns:
            str: Path to the prepared JSONL file
        """
        training_examples = []
        
        # Check if dataset folder exists
        if not os.path.exists(dataset_folder_path):
            raise FileNotFoundError(f"Dataset folder not found: {dataset_folder_path}")
        
        # Process different file types in the dataset folder
        for filename in os.listdir(dataset_folder_path):
            file_path = os.path.join(dataset_folder_path, filename)
            
            if filename.endswith('.json'):
                # Process JSON files containing training examples
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Expect format: [{"submission": "...", "rubric": "...", "score": "...", "feedback": "..."}]
                if isinstance(data, list):
                    for item in data:
                        if all(key in item for key in ['submission', 'rubric', 'score', 'feedback']):
                            training_example = self._create_training_example(
                                item['submission'], 
                                item['rubric'], 
                                item['score'], 
                                item['feedback']
                            )
                            training_examples.append(training_example)
            
            elif filename.endswith('.csv'):
                # Process CSV files
                import csv
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if all(key in row for key in ['submission', 'rubric', 'score', 'feedback']):
                            training_example = self._create_training_example(
                                row['submission'], 
                                row['rubric'], 
                                row['score'], 
                                row['feedback']
                            )
                            training_examples.append(training_example)
        
        if not training_examples:
            raise ValueError("No valid training examples found in the dataset folder")
        
        # Save training data as JSONL file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        training_file_path = os.path.join(self.training_data_folder, f'training_data_{timestamp}.jsonl')
        
        with open(training_file_path, 'w', encoding='utf-8') as f:
            for example in training_examples:
                f.write(json.dumps(example) + '\n')
        
        print(f"Prepared {len(training_examples)} training examples")
        print(f"Training data saved to: {training_file_path}")
        
        return training_file_path
    
    def _create_training_example(self, submission, rubric, score, feedback):
        """
        Create a training example in OpenAI's fine-tuning format.
        """
        from grader.prompts import create_grading_prompt
        
        # Create the prompt using existing prompt template
        prompt = create_grading_prompt("Assignment", submission, rubric)
        
        # Create the expected response
        expected_response = json.dumps({
            "score": str(score),
            "feedback": str(feedback)
        })
        
        return {
            "messages": [
                {"role": "system", "content": "You are an expert grading assistant that evaluates student work based on provided rubrics."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": expected_response}
            ]
        }
    
    def upload_training_file(self, training_file_path):
        """
        Upload training file to OpenAI.
        
        Args:
            training_file_path (str): Path to the training JSONL file
            
        Returns:
            str: File ID from OpenAI
        """
        print(f"Uploading training file: {training_file_path}")
        
        with open(training_file_path, 'rb') as f:
            response = self.client.files.create(
                file=f,
                purpose='fine-tune'
            )
        
        print(f"File uploaded successfully. File ID: {response.id}")
        return response.id
    
    def create_fine_tune_job(self, file_id, model="gpt-3.5-turbo", suffix=None):
        """
        Create a fine-tuning job.
        
        Args:
            file_id (str): ID of the uploaded training file
            model (str): Base model to fine-tune
            suffix (str): Optional suffix for the fine-tuned model name
            
        Returns:
            str: Fine-tuning job ID
        """
        print(f"Creating fine-tuning job with file ID: {file_id}")
        
        job_params = {
            "training_file": file_id,
            "model": model
        }
        
        if suffix:
            job_params["suffix"] = suffix
        
        response = self.client.fine_tuning.jobs.create(**job_params)
        
        print(f"Fine-tuning job created. Job ID: {response.id}")
        print(f"Status: {response.status}")
        
        return response.id
    
    def check_job_status(self, job_id):
        """
        Check the status of a fine-tuning job.
        
        Args:
            job_id (str): Fine-tuning job ID
            
        Returns:
            dict: Job status information
        """
        response = self.client.fine_tuning.jobs.retrieve(job_id)
        
        status_info = {
            "id": response.id,
            "status": response.status,
            "model": response.model,
            "fine_tuned_model": response.fine_tuned_model,
            "created_at": response.created_at,
            "finished_at": response.finished_at
        }
        
        print(f"Job Status: {status_info['status']}")
        if status_info['fine_tuned_model']:
            print(f"Fine-tuned model: {status_info['fine_tuned_model']}")
        
        return status_info
    
    def wait_for_completion(self, job_id, check_interval=60):
        """
        Wait for fine-tuning job to complete.
        
        Args:
            job_id (str): Fine-tuning job ID
            check_interval (int): Seconds between status checks
            
        Returns:
            str: Fine-tuned model ID
        """
        print(f"Waiting for fine-tuning job {job_id} to complete...")
        
        while True:
            status_info = self.check_job_status(job_id)
            
            if status_info['status'] == 'succeeded':
                print(f"Fine-tuning completed! Model: {status_info['fine_tuned_model']}")
                return status_info['fine_tuned_model']
            elif status_info['status'] == 'failed':
                raise Exception(f"Fine-tuning job failed: {job_id}")
            elif status_info['status'] in ['cancelled', 'expired']:
                raise Exception(f"Fine-tuning job {status_info['status']}: {job_id}")
            
            print(f"Status: {status_info['status']}. Checking again in {check_interval} seconds...")
            time.sleep(check_interval)
    
    def update_config_with_model(self, fine_tuned_model_id):
        """
        Update the configuration to use the fine-tuned model.
        
        Args:
            fine_tuned_model_id (str): ID of the fine-tuned model
        """
        # Save the fine-tuned model ID to a config file
        config_file = os.path.join(self.training_data_folder, 'fine_tuned_models.json')
        
        models_config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                models_config = json.load(f)
        
        timestamp = datetime.now().isoformat()
        models_config[timestamp] = {
            "model_id": fine_tuned_model_id,
            "created_at": timestamp,
            "status": "active"
        }
        
        with open(config_file, 'w') as f:
            json.dump(models_config, f, indent=2)
        
        print(f"Fine-tuned model configuration saved: {config_file}")
        print(f"To use this model, update your .env file with: OPENAI_MODEL={fine_tuned_model_id}")

# Convenience function for the complete fine-tuning process
def train_model_on_dataset(dataset_folder_path, model="gpt-3.5-turbo", suffix=None, wait_for_completion=True):
    """
    Complete fine-tuning process from dataset folder to trained model.
    
    Args:
        dataset_folder_path (str): Path to your dataset folder
        model (str): Base model to fine-tune
        suffix (str): Optional suffix for the fine-tuned model name
        wait_for_completion (bool): Whether to wait for training to complete
        
    Returns:
        dict: Training results including job_id and model_id (if completed)
    """
    fine_tuner = GPTFineTuner()
    
    try:
        # Step 1: Prepare training data
        print("Step 1: Preparing training data...")
        training_file_path = fine_tuner.prepare_training_data(dataset_folder_path)
        
        # Step 2: Upload training file
        print("\nStep 2: Uploading training file...")
        file_id = fine_tuner.upload_training_file(training_file_path)
        
        # Step 3: Create fine-tuning job
        print("\nStep 3: Creating fine-tuning job...")
        job_id = fine_tuner.create_fine_tune_job(file_id, model, suffix)
        
        result = {
            "job_id": job_id,
            "file_id": file_id,
            "training_file_path": training_file_path,
            "status": "started"
        }
        
        # Step 4: Wait for completion (optional)
        if wait_for_completion:
            print("\nStep 4: Waiting for training to complete...")
            fine_tuned_model_id = fine_tuner.wait_for_completion(job_id)
            
            # Step 5: Update configuration
            print("\nStep 5: Updating configuration...")
            fine_tuner.update_config_with_model(fine_tuned_model_id)
            
            result["fine_tuned_model_id"] = fine_tuned_model_id
            result["status"] = "completed"
        
        return result
        
    except Exception as e:
        print(f"Error during fine-tuning process: {str(e)}")
        raise