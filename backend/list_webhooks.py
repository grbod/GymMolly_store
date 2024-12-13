import requests
import base64
import os
from dotenv import load_dotenv
from pathlib import Path
import json

# Get the absolute path to the .env file
base_dir = Path(__file__).resolve().parent
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
env_file = '.env.development' if FLASK_ENV == 'development' else '.env.production'
env_path = base_dir / env_file

print(f"Looking for env file at: {env_path}")
load_dotenv(env_path)

# Hardcode the credentials from .env.development for testing
SS_CLIENT_ID = os.getenv('SS_CLIENT_ID', '45aa2753986b4d0ca1679ad67930f403')
SS_CLIENT_SECRET = os.getenv('SS_CLIENT_SECRET', 'b66449b9d3ed461e93896691661b09a3')
SS_STORE_ID = os.getenv('SS_STORE_ID', '85232')

def list_webhooks():
    # Verify credentials are loaded
    if not SS_CLIENT_ID or not SS_CLIENT_SECRET:
        print("Error: Missing ShipStation credentials")
        print(f"Client ID: {'Present' if SS_CLIENT_ID else 'Missing'}")
        print(f"Client Secret: {'Present' if SS_CLIENT_SECRET else 'Missing'}")
        return

    # Create the authorization string
    auth_string = f"{SS_CLIENT_ID}:{SS_CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    # Print debug info (remove sensitive info in production)
    print(f"\nDebug Info:")
    print(f"Auth String (first 10 chars): {auth_string[:10]}...")
    print(f"Encoded Auth (first 20 chars): {encoded_auth[:20]}...")
    
    # API endpoint
    url = "https://ssapi.shipstation.com/webhooks"
    
    # Headers with authentication
    headers = {
        'Host': 'ssapi.shipstation.com',
        'Authorization': f'Basic {encoded_auth}'
    }
    
    try:
        # Make the request
        print("\nMaking request to ShipStation API...")
        response = requests.get(url, headers=headers)
        
        # Check if request was successful
        if response.status_code == 200:
            webhooks = response.json()
            print("\nRegistered Webhooks:")
            print("===================")
            
            # Check if webhooks is a list
            if isinstance(webhooks, list):
                if not webhooks:
                    print("No webhooks found.")
                else:
                    for webhook in webhooks:
                        if isinstance(webhook, dict):
                            print(f"\nWebhook ID: {webhook.get('WebHookId')}")
                            print(f"Store ID: {webhook.get('StoreId')}")
                            print(f"Name: {webhook.get('Name')}")
                            print(f"URL: {webhook.get('Url')}")
                            print(f"Event: {webhook.get('Event')}")
                            print(f"Active: {webhook.get('Active')}")
                            print("-------------------")
            else:
                print("Raw response:")
                print(json.dumps(webhooks, indent=2))
        else:
            print(f"\nError: {response.status_code}")
            print(f"Response: {response.text}")
            print("\nRequest Headers:")
            print(headers)
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print("Full error details:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"Using credentials from: {env_file}")
    print(f"Store ID: {SS_STORE_ID}")
    print(f"Client ID exists: {'Yes' if SS_CLIENT_ID else 'No'}")
    print(f"Client Secret exists: {'Yes' if SS_CLIENT_SECRET else 'No'}")
    list_webhooks()
