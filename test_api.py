import requests
import os
from dotenv import load_dotenv

def test_api():
    load_dotenv()
    api_key = os.getenv('OMDB_API_KEY')
    print(f"API Key length: {len(api_key) if api_key else 'None'}")
    
    url = "http://www.omdbapi.com/"
    params = {
        'apikey': api_key,
        't': 'Aftersun',
        'type': 'movie',
        'r': 'json'
    }
    
    response = requests.get(url, params=params)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_api() 