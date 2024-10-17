import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///rules.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300
    RATELIMIT_DEFAULT = "100/day;10/hour;1/minute"
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI') or "memory://"