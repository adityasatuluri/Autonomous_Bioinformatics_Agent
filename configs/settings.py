import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-for-mvp')
    # Use a relative path from the app root
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(BASE_DIR, 'storage', 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # External APIs
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    
    # Path to data
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    GSE68086_DIR = os.path.join(DATA_DIR, 'GSE68086')

    # Security & Request Limits
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB maximum request body
    ALLOWED_DATASETS = {'GSE68086', 'GSE68086 Platelet RNA-Seq'}
    MIN_QUESTION_LENGTH = 5
    MAX_QUESTION_LENGTH = 2000

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Export the active configuration
config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    default=DevelopmentConfig
)
