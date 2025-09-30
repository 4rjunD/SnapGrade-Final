import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration settings
class Config:
    # OpenAI API configuration (for Vision/OCR only)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_VISION_MODEL = os.getenv('OPENAI_VISION_MODEL', 'gpt-4o')  # For OCR only
    
    # Google Gemini API configuration (for grading)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAli4sgSxkaJkrGkgJlXGtGLgWRfGP3kgY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')
    
    # Legacy - keeping for backward compatibility
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
    
    # Dropbox configuration
    DROPBOX_ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')
    
    # Tesseract configuration (for OCR)
    TESSERACT_PATH = os.getenv('TESSERACT_PATH')
    
    # Flask configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', '8080'))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB by default
    
    # Assignment folder configuration
    ASSIGNMENT_FOLDER = os.getenv('ASSIGNMENT_FOLDER', 'assignment')
    
    # Email configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@snapgrade.com')
    CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', 'tejash.gupta045@gmail.com')