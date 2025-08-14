# Rubiq - AI-Powered Grading Platform

Rubiq is a B2B AI grading platform for schools and edtech companies. It uses GPT-4 (or Claude) to automatically grade assignments like essays, short answers, and problem sets based on customizable rubrics. Teachers can upload a submission, select or input a rubric, and Rubiq generates a score and detailed feedback instantly.

## Features

- Automatic grading of various assignment types (essays, short answers, problem sets, etc.)
- Customizable rubrics for different assignment types
- Support for text submissions and image uploads (with OCR)
- Integration with Dropbox for file handling
- Clean API for integration with existing LMS systems
- Simple frontend for demoing and school adoption

## Project Structure

```
├── app.py                  # Main Flask application
├── config.py               # Configuration settings
├── grader/                 # Grading engine
│   ├── __init__.py
│   ├── engine.py           # Core grading functionality
│   └── prompts.py          # GPT prompts for grading
├── image_processor/        # Image processing utilities
│   ├── __init__.py
│   ├── dropbox_handler.py  # Dropbox integration
│   └── ocr.py              # Optical Character Recognition
├── process_assignments.py  # Batch processing script
├── static/                 # Static assets
│   ├── css/
│   │   └── style.css       # Custom styles
│   └── js/
│       └── main.js         # Frontend JavaScript
├── templates/              # HTML templates
│   └── index.html          # Main frontend interface
└── requirements.txt        # Python dependencies
```

## Setup Instructions

### Prerequisites

- Python 3.6 or higher
- OpenAI API key
- Tesseract OCR (optional, for image processing)
- Dropbox API key (optional, for Dropbox integration)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/rubiq.git
   cd rubiq
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4
   DEBUG=True
   HOST=0.0.0.0
   PORT=5000
   UPLOAD_FOLDER=uploads
   ASSIGNMENT_FOLDER=assignment
   TESSERACT_PATH=/usr/local/bin/tesseract  # Path to Tesseract OCR executable
   DROPBOX_ACCESS_TOKEN=your_dropbox_token  # Optional
   ```

### Running the Application

1. Start the Flask server:
   ```
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## API Endpoints

### Grade Text Submission

```
POST /grade

Request Body:
{
    "assignment_type": "Essay",
    "submission": "Student's answer text here",
    "rubric": "Detailed grading rubric here"
}

Response:
{
    "score": 95,
    "feedback": "Excellent structure and clarity. Minor grammar errors."
}
```

### Grade Image Submission

```
POST /grade-image

Request Body:
{
    "assignment_type": "Essay",
    "image_file": "base64_encoded_image_data",
    "rubric": "Detailed grading rubric here"
}

Response:
{
    "score": 95,
    "feedback": "Excellent structure and clarity. Minor grammar errors.",
    "extracted_text": "The text extracted from the image"
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.