# INTENTIONALLY VULNERABLE — AI / training fixture only.
import requests


def fetch(url: str):
    return requests.get(url, verify=False).text
