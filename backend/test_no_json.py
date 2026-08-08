import httpx
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

def test_no_json_mode(model):
    print(f"Testing {model} without json_mode...")
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Reply with JSON: {\"status\": \"ok\"}"}
        ],
        "max_tokens": 2000,
        "temperature": 0.0
    }
    
    resp = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=60)
    print(f"[{resp.status_code}] {resp.text}")

test_no_json_mode("openai/gpt-oss-20b")
test_no_json_mode("openai/gpt-oss-120b")
test_no_json_mode("allam-2-7b")
test_no_json_mode("groq/compound")
test_no_json_mode("qwen/qwen3.6-27b")
