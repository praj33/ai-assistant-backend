"""
Keep-alive script to prevent Render free tier from sleeping
Pings the health endpoint every 14 minutes
"""

import requests
import time
import os
from datetime import datetime

BACKEND_URL = os.getenv("BACKEND_URL", "https://ai-assistant-backend-8hur.onrender.com")
PING_INTERVAL = 14 * 60  # 14 minutes in seconds

def ping_server():
    """Ping the health endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            print(f"[{datetime.now()}] OK Server is alive")
            return True
        else:
            print(f"[{datetime.now()}] ERROR Server returned {response.status_code}")
            return False
    except Exception as e:
        print(f"[{datetime.now()}] ERROR Ping failed: {e}")
        return False

if __name__ == "__main__":
    print(f"Starting keep-alive for {BACKEND_URL}")
    print(f"Pinging every {PING_INTERVAL // 60} minutes")
    
    while True:
        ping_server()
        time.sleep(PING_INTERVAL)
