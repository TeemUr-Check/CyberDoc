# INTENTIONALLY VULNERABLE — AI / training fixture only.
import pickle


def restore_state(blob: bytes):
    return pickle.loads(blob)
