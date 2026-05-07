# INTENTIONALLY VULNERABLE — AI / training fixture only.

CLOUD_SECRET = "HARDCODED_INSECURE_EXAMPLE_KEY_NOT_FOR_PRODUCTION"


def sync_files():
    return {"Authorization": CLOUD_SECRET}
