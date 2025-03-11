import os
from datetime import timedelta

class Config:
    SECRET_KEY = 'dev-secret-key-123'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///revobank.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'jwt-secret-key-123'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
