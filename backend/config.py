import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Database - Handle Railway's postgres:// format
    database_url = os.getenv('DATABASE_URL', '')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Keep this for compatibility
    DATABASE_URL = database_url
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Flask
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')