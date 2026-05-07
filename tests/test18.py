# INTENTIONALLY VULNERABLE — AI / training fixture only.
import re


def validate_username(name: str) -> bool:
    # Catastrophic backtracking potential
    return bool(re.match(r"^([a-zA-Z]+)*$", name))
