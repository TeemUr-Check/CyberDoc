import requests
import json

payload = {"input_value": "hello", "output_type": "chat", "input_type": "chat"}
headers = {"Content-Type": "application/json", "x-api-key": "sk-0G2SrJ5z7cHWpiShAPIyTMsaQEn1SSFWdiM3TsQSguo"}
r = requests.post(
    "http://localhost:7860/api/v1/run/1191ec74-9836-4f45-bb70-a7ee729f3d18",
    json=payload,
    headers=headers,
    timeout=120,
)
print(f"Status: {r.status_code}")
print(f"Type: {r.headers.get('content-type', '?')}")
print(r.text[:1500])
