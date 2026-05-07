# INTENTIONALLY VULNERABLE — AI / training fixture only.
import base64
import json


def decode_jwt_unsafe(token: str):
    h, p, _ = token.split(".")
    return json.loads(base64.urlsafe_b64decode(p + "=="))
