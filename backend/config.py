from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Flask and Database Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://gymmollydb_user:4XMPoJDqyYtotaUjlkItXaQuaeR4wV2C@dpg-csgqbdo8fa8c7391s130-a/gymmollydb'
db = SQLAlchemy(app)



# ShipStation API Configuration
SS_CLIENT_ID = "74e67f0a1af04427826865a889eaa00e"
SS_CLIENT_SECRET = "3d5f84c662e647c78f6abffc496e688b"
SS_BASE_URL = "https://ssapi.shipstation.com"
SS_STORE_ID = 85232


