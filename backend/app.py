from config import app, db
from main import *  # Import all models and routes

if __name__ == '__main__':
    app.run(debug=True, port=5001) 