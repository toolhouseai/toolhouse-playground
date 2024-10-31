from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
import base64
import json
import os

def decrypt(enc):
    enc = base64.b64decode(enc)
    secret = os.environ.get("PLAYGROUND_SECRET_TOKEN")
    cipher = AES.new(secret.encode('utf-8'), AES.MODE_ECB)
    out = unpad(cipher.decrypt(enc), 16)
    return json.loads(out)