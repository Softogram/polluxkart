import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

class Settings:
    # MongoDB
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME: str = os.environ.get('DB_NAME', 'polluxkart')
    
    # JWT
    JWT_SECRET: str = os.environ.get('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRATION_HOURS: int = 24
    
    # Razorpay
    RAZORPAY_KEY_ID: str = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET: str = os.environ.get('RAZORPAY_KEY_SECRET', '')
    RAZORPAY_WEBHOOK_SECRET: str = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')
    
    # Email (SMTP)
    SMTP_HOST: str = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER: str = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD: str = os.environ.get('SMTP_PASSWORD', '')
    EMAIL_FROM: str = os.environ.get('EMAIL_FROM', 'noreply@polluxkart.com')
    
    # CORS
    CORS_ORIGINS: str = os.environ.get('CORS_ORIGINS', '*')
    
    # App
    APP_NAME: str = 'PolluxKart API'
    APP_VERSION: str = '1.0.0'
    DEBUG: bool = os.environ.get('DEBUG', 'false').lower() == 'true'

settings = Settings()
