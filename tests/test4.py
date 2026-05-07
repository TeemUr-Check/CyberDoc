# INTENTIONALLY VULNERABLE — AI / training fixture only.

def read_report(filename: str) -> bytes:
    path = "/var/reports/" + filename
    with open(path, "rb") as f:
        return f.read()
