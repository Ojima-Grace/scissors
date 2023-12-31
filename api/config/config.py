import os
from decouple import config
from datetime import timedelta
from flask_caching import Cache, SimpleCache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

uri = config('DATABASE_URL')
if uri.startswith('postgres://'):
    uri = uri.replace('postgres://', 'postgresql://', 1)

# CACHE_TYPE = 'redis'
# CACHE_REDIS_URL = 'redis://localhost:6379/0'
# CACHE_DEFAULT_TIME = 300
# cache = Cache(config={'CACHE_TYPE': CACHE_TYPE, 'CACHE_REDIS_URL': CACHE_REDIS_URL}, with_jinja2_ext=False)

# limiter = Limiter(
#   get_remote_address,
#   storage_uri="redis://localhost:6379",
#   storage_options={"socket_connect_timeout": 30},
#   strategy="fixed-window"
# )

CACHE_DEFAULT_TIMEOUT = 300  # Cache timeout in seconds

cache = Cache(config={'CACHE_TYPE': 'SimpleCache'}, with_jinja2_ext=False)

simCache = SimpleCache()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "50 per hour"]
)
limiter._storage_backend = cache

class Config:
    SECRET_KEY = config('SECRET_KEY', 'secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=45)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(minutes=45)
    JWT_SECRET_KEY = config('JWT_SECRET_KEY')

class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    
class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'+os.path.join(BASE_DIR, 'db.sqlite3')

class ProdConfig(Config):
    SQLALCHEMY_DATABASE_URI = uri 
    SQLALCHEMY_TRACK_MODIFICATION = False
    DEBUG = config('DEBUG', False, cast=bool)


config_dict = {
    'dev': DevConfig,
    'prod': ProdConfig,
    'test': TestConfig
}