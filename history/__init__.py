import requests

base_url = "http://0.0.0.0:8000/v1"


def url(path: str):
    return base_url + path


def convert_to_json(obj):
    if isinstance(obj, dict):
        return {k: convert_to_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json(item) for item in obj]
    elif hasattr(obj, "model_dump"):
        return obj.model_dump()
    else:
        return obj


def get_chat_history(chat_id, api_key):
    try:
        request = requests.get(
            url(f"/chats/{chat_id}"), headers={"Authorization": f"Bearer {api_key}"}
        )
        request.raise_for_status()
        body = request.json()
        return body.get("history")
    except Exception as e:
        return None


def get_all_chats(api_key):
    try:
        request = requests.get(
            url(f"/chats"), headers={"Authorization": f"Bearer {api_key}"}
        )
        request.raise_for_status()
        return request.json()
    except Exception as e:
        return None


def save_chat_history(messages, api_key):
    try:
        converted = convert_to_json(messages)
        response = requests.post(
            url("/chats"),
            headers={"Authorization": f"Bearer {api_key}"},
            json={"history": converted},
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(e)
        return None


def update_chat_history(chat_id, messages, api_key):
    try:
        converted = convert_to_json(messages)
        response = requests.put(
            url(f"/chats/{chat_id}"),
            headers={"Authorization": f"Bearer {api_key}"},
            json={"history": converted},
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(e)
        return None


def upsert_chat_history(chat_id, messages, api_key):
    if not chat_id:
        return save_chat_history(messages, api_key)
    else:
        return update_chat_history(chat_id, messages, api_key)


def delete_chat_history(chat_id, api_key):
    try:
        request = requests.delete(
            url(f"/chats/{chat_id}"),
            headers={"Authorization": f"Bearer {api_key}"},
        )
        request.raise_for_status()
        return True
    except Exception as e:
        return False
