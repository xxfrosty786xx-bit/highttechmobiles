import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'high-tech-mobile-super-secret-key-2026-prod-jwt-safe')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400 * 7 # 7 days
    
    # Database
    DATABASE_PATH = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'hightechmobile.db'))
    
    # Store Profile
    STORE_NAME = os.environ.get('STORE_NAME', 'HIGH TECH MOBILE')
    ADMIN_NAME = os.environ.get('ADMIN_NAME', 'Avid Malik & Danish Malik')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'avidmalikhts@gmail.com')
    ADMIN_DEFAULT_PASSWORD = os.environ.get('ADMIN_DEFAULT_PASSWORD', 'nayra@99667')
    
    # Localization & Currency
    CURRENCY_CODE = 'INR'
    CURRENCY_SYMBOL = '₹'
    TIMEZONE = 'Asia/Kolkata'
    
    # Payment Gateway (Razorpay)
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
    
    # Uploads
    UPLOAD_FOLDER = str(BASE_DIR / 'static' / 'images' / 'products')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
