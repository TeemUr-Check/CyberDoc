"""
INTENTIONALLY VULNERABLE — AI / training fixture only.
"""


def diagnose(path: str) -> str:
    try:
        import os

        os.remove(path)
    except Exception as e:
        return repr(e)
