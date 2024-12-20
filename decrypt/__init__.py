from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
import base64
import os


def decrypt(enc):
    try:
        enc = base64.b64decode(enc)
        secret = os.environ.get("PLAYGROUND_SECRET_TOKEN")
        cipher = AES.new(secret.encode("utf-8"), AES.MODE_ECB)
        out = unpad(cipher.decrypt(enc), 16)
        return out.decode()
    except:
        return None
