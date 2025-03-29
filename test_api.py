import requests

API_KEY = '652192adb22c4fae65307ae1'
API_URL = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD'

def test_api():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Raise an error if the request fails
        data = response.json()
        print(data)  # Print the full API response to see the structure
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

test_api()

