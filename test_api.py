import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("LAWS_AFRICA_TOKEN")
BASE_URL = "https://api.laws.africa/v3"

def test_fetch_popia_expression():
    # South Africa POPIA Act 4 of 2013 - English Expression
    url = f"{BASE_URL}/akn/za/act/2013/4/@/expression/eng/.json"
    
    headers = {
        "Authorization": f"Token {TOKEN}"
    }
    
    print(f"Fetching from: {url}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("Successfully fetched POPIA full text!")
        # Print the first few characters of the content
        content = data.get('content', '')
        print(f"Content length: {len(content)}")
        print(f"Snippet: {content[:200]}...")
    else:
        print(f"Failed to fetch POPIA. Status code: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_fetch_popia_expression()
