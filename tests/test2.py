# INTENTIONALLY VULNERABLE — AI / training fixture only.
import subprocess

def ping_host(host: str) -> str:
    return subprocess.check_output(f"ping -c 1 {host}", shell=True, text=True)
