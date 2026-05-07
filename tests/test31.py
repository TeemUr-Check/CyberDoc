# INTENTIONALLY VULNERABLE — AI / training fixture only.


def build_redirect(location: str):
    return "HTTP/1.1 302 Found\r\nLocation: " + location + "\r\n\r\n"
