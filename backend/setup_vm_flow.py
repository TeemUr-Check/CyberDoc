import httpx
import json
import sys

BASE_URL = "http://127.0.0.1:7860/api/v1"
MISTRAL_KEY = "EwN6hysonIjXswjs2pvaTUdKVNI1V5Cs"

def setup():
    print(f"[*] Connecting to LangFlow at {BASE_URL}...")
    
    client = httpx.Client(timeout=30.0)
    headers = {"Content-Type": "application/json"}
    
    # 1. Try to login (LangFlow default is langflow/langflow)
    token = None
    try:
        print("[*] Attempting login with default credentials (langflow/langflow)...")
        login_resp = client.post(
            f"{BASE_URL}/login", 
            data={"username": "langflow", "password": "langflow"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            headers["Authorization"] = f"Bearer {token}"
            print("[+] Login successful!")
        else:
            print(f"[!] Login failed ({login_resp.status_code}). Proceeding without token...")
    except Exception as e:
        print(f"[!] Login error: {e}. Proceeding without token...")

    try:
        # 2. Check if flow already exists
        print("[*] Checking for existing CyberDoc flow...")
        flows_resp = client.get(f"{BASE_URL}/flows/", headers=headers)
        if flows_resp.status_code == 200:
            for flow in flows_resp.json():
                if flow["name"] == "CyberDoc Chatbot":
                    print(f"[+] Found existing flow! ID: {flow['id']}")
                    print_instructions(flow['id'])
                    return

        # 3. Create a new flow if not found
        print("[*] Creating new CyberDoc Chatbot flow...")
        flow_data = {
            "name": "CyberDoc Chatbot",
            "description": "AI Assistant for CyberDoc Pro",
            "data": {
                "nodes": [
                    {
                        "id": "MistralAI-1",
                        "data": {
                            "type": "MistralAI",
                            "node": {
                                "template": {
                                    "mistral_api_key": {"value": MISTRAL_KEY},
                                    "model_name": {"value": "codestral-latest"},
                                    "system_message": {"value": "Ты - эксперт по ИБ ассистент платформы CyberDoc Pro. Отвечай кратко и профессионально."}
                                }
                            }
                        }
                    },
                    {
                        "id": "ChatInput-1",
                        "data": {"type": "ChatInput", "node": {"template": {}}}
                    },
                    {
                        "id": "ChatOutput-1",
                        "data": {"type": "ChatOutput", "node": {"template": {}}}
                    }
                ],
                "edges": [
                    {"source": "ChatInput-1", "target": "MistralAI-1"},
                    {"source": "MistralAI-1", "target": "ChatOutput-1"}
                ]
            }
        }
        
        resp = client.post(f"{BASE_URL}/flows/", json=flow_data, headers=headers)
        if resp.status_code in (201, 200):
            new_id = resp.json()["id"]
            print(f"\n[+] SUCCESS! New Flow created.")
            print_instructions(new_id)
        else:
            print(f"[-] Error creating flow: {resp.status_code} {resp.text}")
            print("\n[TIP] Try to open http://localhost:7860 in Kali browser and create a flow manually named 'CyberDoc Chatbot'")
    except Exception as e:
        print(f"[-] Connection failed: {e}")

def print_instructions(flow_id):
    print(f"\n[!] YOUR FLOW_ID: {flow_id}")
    print(f"\n[#] Run your backend with this command sequence:")
    print("-" * 50)
    print(f"export LANGFLOW_FLOW_ID=\"{flow_id}\"")
    print(f"export LANGFLOW_API_URL=\"{BASE_URL}/run\"")
    print(f"export FRONTEND_DIR=\"../frontend\"")
    print(f"uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("-" * 50)

if __name__ == "__main__":
    setup()
