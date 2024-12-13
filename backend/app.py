from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import app, db
from main import *  # Import all models and routes

if __name__ == '__main__':
    app.run(debug=True) 