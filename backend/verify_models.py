import httpx
import json
import os

API_KEY = os.getenv("GROQ_API_KEY")
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

MODELS = [
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
    "groq/compound",
    "groq/compound-mini",
    "qwen/qwen3.6-27b",
    "allam-2-7b",
    "canopylabs/orpheus-v1-english"
]

def test_model(model_name):
    print(f"Testing {model_name}...")
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Reply with JSON: {\"status\": \"ok\"}"}
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 50,
        "temperature": 0.0
    }
    
    try:
        resp = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"  [PASS] HTTP 200 - {resp.json()['choices'][0]['message']['content']}")
            return True
        else:
            print(f"  [FAIL] HTTP {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

for m in MODELS:
    test_model(m)
