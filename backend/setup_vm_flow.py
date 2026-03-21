import httpx
import json
import sys

BASE_URL = "http://127.0.0.1:7860/api/v1"
MISTRAL_KEY = "EwN6hysonIjXswjs2pvaTUdKVNI1V5Cs"

def setup():
    print(f"[*] Connecting to LangFlow at {BASE_URL}...")
    try:
        # 1. Create a new flow
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
        
        resp = httpx.post(f"{BASE_URL}/flows/", json=flow_data, timeout=20.0)
        if resp.status_code == 201:
            new_id = resp.json()["id"]
            print(f"\n[+] SUCCESS! New Flow created.")
            print(f"[!] YOUR NEW FLOW_ID: {new_id}")
            print(f"\n[#] Now run your backend with this command:")
            print(f"export LANGFLOW_FLOW_ID=\"{new_id}\"")
            print(f"uvicorn app.main:app --host 0.0.0.0 --port 8000")
        else:
            print(f"[-] Error creating flow: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        print("[?] Is LangFlow Docker container running? (sudo docker ps)")

if __name__ == "__main__":
    setup()
