# INTENTIONALLY VULNERABLE — AI / training fixture only.
import hashlib


def check_password(pw: str, stored: str) -> bool:
    return hashlib.md5(pw.encode()).hexdigest() == stored
