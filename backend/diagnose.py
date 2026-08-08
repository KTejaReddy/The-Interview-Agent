import httpx
import uuid
import time
from rich.console import Console
console = Console()

API_URL = "http://127.0.0.1:8005/api/interview"
session_id = str(uuid.uuid4())

console.print(f"Starting session {session_id}...")
start_time = time.time()

try:
    resp = httpx.post(API_URL, json={
        "sessionId": session_id,
        "candidate": {"member": {"id": "CAND-001"}}
    }, timeout=120)
    
    console.print(f"Start Response ({time.time() - start_time:.2f}s): {resp.status_code}")
    console.print(resp.json())
    
    if resp.status_code == 200:
        start_time = time.time()
        console.print("\nSending message...")
        msg_resp = httpx.post(API_URL, json={
            "sessionId": session_id,
            "message": "I don't know much about this."
        }, timeout=120)
        
        console.print(f"Message Response ({time.time() - start_time:.2f}s): {msg_resp.status_code}")
        console.print(msg_resp.json())
except Exception as e:
    console.print(f"Error: {e}")
