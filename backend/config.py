import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables based on FLASK_ENV
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
env_file = '.env.production' if FLASK_ENV == 'production' else '.env.development'
load_dotenv(env_file)

class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///dev.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLAlchemy performance settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {
            'check_same_thread': False,
            'timeout': 15
        }
    }

    # ShipStation
    SS_CLIENT_ID = os.getenv('SS_CLIENT_ID')
    SS_CLIENT_SECRET = os.getenv('SS_CLIENT_SECRET')
    SS_BASE_URL = os.getenv('SS_BASE_URL', 'https://ssapi.shipstation.com')
    SS_STORE_ID = os.getenv('SS_STORE_ID')
    
    # Session configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'gymmolly-secret-key-2024')
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    
    # Master password for authentication
    MASTER_PASSWORD = 'MIAMI'

# Initialize Flask app with config
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Export ShipStation config for other modules
SS_CLIENT_ID = Config.SS_CLIENT_ID
SS_CLIENT_SECRET = Config.SS_CLIENT_SECRET
SS_BASE_URL = Config.SS_BASE_URL
SS_STORE_ID = Config.SS_STORE_ID


