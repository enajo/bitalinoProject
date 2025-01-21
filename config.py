import os

class Config:
    """Base configuration class."""
    
    # Secret key for sessions and CSRF protection (you should set it to a secure value in production)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here'

    # Database URI (SQLite for development, change it for production)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    
    # Disable tracking of modifications to objects (to save memory)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload folder for files (specifically text files in this case)
    UPLOAD_FOLDER = 'uploads'
    
    # Allowed file extensions for upload (ensure only text files are allowed)
    ALLOWED_EXTENSIONS = {'txt'}
    
    # Maximum content length for uploaded files (1MB for example)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # Flask-WTF CSRF protection settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('CSRF_SECRET_KEY') or 'your_csrf_secret_key_here'


class ProductionConfig(Config):
    """Production specific configuration."""
    
    # Enable production features
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Development specific configuration."""
    
    # Enable development features
    DEBUG = True
    TESTING = True
    SQLALCHEMY_ECHO = True  # Echo SQL queries to the console


class TestingConfig(Config):
    """Testing specific configuration."""
    
    # Use an in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True
    DEBUG = False


# Environment-based configuration (you can switch between development, production, or testing)
config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
    'test': TestingConfig
}
