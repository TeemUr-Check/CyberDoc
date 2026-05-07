# INTENTIONALLY VULNERABLE — AI / training fixture only.

def redirect_next(request_next: str):
    from flask import redirect
    return redirect(request_next)
