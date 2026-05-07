# INTENTIONALLY VULNERABLE — AI / training fixture only.
import requests


def preview_link(url: str) -> str:
    r = requests.get(url, timeout=5)
    return r.text[:2000]
