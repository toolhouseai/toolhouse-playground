import requests
import os
import traceback


def get_api_key(jwt):
    try:
        url = os.environ.get("USER_API_BASE_URL") + "/me/api-keys/default"
        response = requests.get(url, headers={"Authorization": f"Bearer {jwt}"})
        response.raise_for_status()
        api_key = response.json()
        return api_key.get("api_key")
    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()
        return None
