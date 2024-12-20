import os


def build_url(chat_id):
    base_url = os.environ.get("PLAYGROUND_BASE_URL")
    return (
        f"{base_url}?chat={chat_id}"
        if os.environ.get("ENVIRONMENT") == "development"
        else f"{base_url}/c/{chat_id}"
    )
