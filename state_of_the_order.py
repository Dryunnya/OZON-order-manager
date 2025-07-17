import requests
import json
from token_site import SCLAD_HEADERS


url = 'https://api.moysklad.ru/api/remap/1.2/entity/customerorder/metadata'

try:
    response = requests.get(url, headers=SCLAD_HEADERS)
    response.raise_for_status()
    metadata = response.json()
    states = metadata.get('states', [])

    if states:
        for state in states:
            print(f"name: {state.get('name')}, id: {state.get('id')}")
    else:
        print("States information not found in metadata.")

except requests.exceptions.RequestException as e:
    print(f"Error getting customer order meta{e}")
    if 'response' in locals() and response:
        print(f"Response Text: {response.text}")
except json.JSONDecodeError:
    print("Error decoding JSON response.")
    if 'response' in locals() and response:
        print(f"Response Text: {response.text}")


