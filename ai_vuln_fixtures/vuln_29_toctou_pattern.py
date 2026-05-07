# INTENTIONALLY VULNERABLE — AI / training fixture only.
import os


def safe_read(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError
    # race: path may be replaced between check and open
    return open(path, "rb").read()
