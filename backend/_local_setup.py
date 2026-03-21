import httpx
import json
import sys
import os

os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

BASE_URL = "http://127.0.0.1:7860/api/v1"
MISTRAL_KEY = "EwN6hysonIjXswjs2pvaTUdKVNI1V5Cs"

def setup():
    print(f"[*] Connecting to LangFlow at {BASE_URL}...")
    client = httpx.Client(timeout=30.0, verify=False, proxy=None)
    headers = {"Content-Type": "application/json"}

    # Login
    print("[*] Logging in...")
    try:
        login_resp = client.post(
            f"{BASE_URL}/login",
            data={"username": "langflow", "password": "langflow"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            headers["Authorization"] = f"Bearer {token}"
            print("[+] Login OK")
        else:
            print(f"[!] Login returned {login_resp.status_code}: {login_resp.text[:200]}")
    except Exception as e:
        print(f"[!] Login error: {e}")
        return

    # Check existing flows
    print("[*] Listing flows...")
    try:
        flows_resp = client.get(f"{BASE_URL}/flows/", headers=headers)
        if flows_resp.status_code == 200:
            flows = flows_resp.json()
            for f in flows:
                if f.get("name") == "CyberDoc Chatbot":
                    fid = f["id"]
                    print(f"[+] Found existing CyberDoc Chatbot flow: {fid}")
                    show(fid)
                    return
        print(f"[*] No existing CyberDoc flow found ({len(flows)} flows total)")
    except Exception as e:
        print(f"[!] List flows error: {e}")

    # Create flow
    print("[*] Creating CyberDoc Chatbot flow...")
    flow_payload = {
        "name": "CyberDoc Chatbot",
        "description": "AI cybersecurity assistant",
        "data": {
            "nodes": [
                {"id": "ChatInput-1", "data": {"type": "ChatInput", "node": {"template": {}}}},
                {"id": "ChatOutput-1", "data": {"type": "ChatOutput", "node": {"template": {}}}},
                {
                    "id": "MistralAI-1",
                    "data": {
                        "type": "MistralAI",
                        "node": {
                            "template": {
                                "mistral_api_key": {"value": MISTRAL_KEY},
                                "model_name": {"value": "codestral-latest"},
                                "system_message": {"value": "You are CyberDoc Pro AI assistant. Help users with cybersecurity questions. Answer concisely in Russian."},
                            }
                        },
                    },
                },
            ],
            "edges": [
                {"source": "ChatInput-1", "target": "MistralAI-1"},
                {"source": "MistralAI-1", "target": "ChatOutput-1"},
            ],
        },
    }
    try:
        resp = client.post(f"{BASE_URL}/flows/", json=flow_payload, headers=headers)
        if resp.status_code in (200, 201):
            fid = resp.json()["id"]
            print(f"[+] Flow created: {fid}")
            show(fid)
        else:
            print(f"[-] Create failed {resp.status_code}: {resp.text[:300]}")
    except Exception as e:
        print(f"[-] Create error: {e}")

    # Generate API key
    print("[*] Generating API key...")
    try:
        key_resp = client.post(f"{BASE_URL}/api_key/", json={"name": "cyberdoc"}, headers=headers)
        if key_resp.status_code in (200, 201):
            api_key = key_resp.json().get("api_key", "")
            print(f"[+] API Key: {api_key}")
        else:
            print(f"[!] API key generation: {key_resp.status_code}")
    except Exception as e:
        print(f"[!] API key error: {e}")


def show(fid):
    print(f"\n{'='*50}")
    print(f"FLOW_ID = {fid}")
    print(f"{'='*50}")


if __name__ == "__main__":
    setup()
