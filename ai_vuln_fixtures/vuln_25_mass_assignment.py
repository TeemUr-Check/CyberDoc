# INTENTIONALLY VULNERABLE — AI / training fixture only.


def update_profile(user, body: dict):
    for k, v in body.items():
        setattr(user, k, v)
    return user
