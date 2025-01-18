import requests

def test_api():
    url = "http://localhost:8000/api/status"
    headers = {
        "X-API-Key": "valid-test-key"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_api()
