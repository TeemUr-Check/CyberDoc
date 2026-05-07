# INTENTIONALLY VULNERABLE — AI / training fixture only.
import random
import string


def new_session_token() -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(16))
