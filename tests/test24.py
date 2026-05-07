# INTENTIONALLY VULNERABLE — AI / training fixture only.


def verify_token(expected: bytes, provided: bytes) -> bool:
    return expected == provided  # non-constant-time compare
