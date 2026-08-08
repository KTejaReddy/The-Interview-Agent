import httpx
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

headers = {"Authorization": f"Bearer {API_KEY}"}
resp = httpx.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=10)
for model in resp.json()['data']:
    print(model['id'])
