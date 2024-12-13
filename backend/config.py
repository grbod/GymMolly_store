import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_migrate import Migrate

# Load environment variables based on FLASK_ENV
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
env_file = '.env.production' if FLASK_ENV == 'production' else '.env.development'
load_dotenv(env_file)

# Flask and Database Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///dev.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ShipStation API Configuration
SS_CLIENT_ID = os.getenv('SS_CLIENT_ID')
SS_CLIENT_SECRET = os.getenv('SS_CLIENT_SECRET')
SS_BASE_URL = os.getenv('SS_BASE_URL', 'https://ssapi.shipstation.com')
SS_STORE_ID = os.getenv('SS_STORE_ID')


