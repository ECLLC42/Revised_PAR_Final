import os
from dotenv import load_dotenv
import ssl

load_dotenv()  # This will load variables from .env file

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')  # Replace with a secure key in production
    DEBUG = os.environ.get('FLASK_ENV') == 'development'

    # File storage configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or './uploads'
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER') or './outputs'

    # S3 configuration
    S3_BUCKET = os.environ.get('S3_BUCKET', 'parproject')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_DEFAULT_REGION') or 'us-east-2'  # Use AWS_DEFAULT_REGION instead of AWS_REGION

    # Session configuration
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True

    @staticmethod
    def init_app(app):
        pass

    # Use this if you need to disable SSL certificate verification (not recommended for production)
    # CELERY_BROKER_USE_SSL = {'ssl_cert_reqs': ssl.CERT_NONE}
    # CELERY_REDIS_BACKEND_USE_SSL = {'ssl_cert_reqs': ssl.CERT_NONE}

config = Config()

# Add this line to make 'config' importable
__all__ = ['config']
