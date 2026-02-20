import os
import requests
import json

print("=" * 70)
print("Production Test - Email & WhatsApp on Render")
print("=" * 70)

BACKEND_URL = os.getenv("BACKEND_URL", "https://ai-assistant-backend-70rt.onrender.com")
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    print("ERROR: API_KEY environment variable must be set to run production tests.")
    print("Usage: API_KEY=your_key python test_production.py")
    exit(1)

# Test 1: Email
print("\n[TEST 1] Email Execution")
print("-" * 70)

email_request = {
    "version": "3.0.0",
    "input": {
        "message": "Send email to blackholeinfiverse20@gmail.com saying 'Production test from Render!'"
    },
    "context": {"platform": "web"}
}

try:
    response = requests.post(
        f"{BACKEND_URL}/api/assistant",
        headers={"Content-Type": "application/json", "X-API-Key": API_KEY},
        json=email_request,
        timeout=60
    )
    
    result = response.json()
    task = result.get("result", {}).get("task", {})
    execution = task.get("execution", {})
    
    print(f"Status: {response.status_code}")
    print(f"Execution Status: {execution.get('status', 'not_executed')}")
    print(f"Response: {result.get('result', {}).get('response')}")
    
    if execution.get('status') == 'success':
        print("\n✅ EMAIL WORKING ON PRODUCTION!")
    else:
        print(f"\n❌ Email failed: {execution.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: WhatsApp
print("\n\n[TEST 2] WhatsApp Execution")
print("-" * 70)

whatsapp_request = {
    "version": "3.0.0",
    "input": {
        "message": "Send WhatsApp to +919004484490 saying 'Production test from Render!'"
    },
    "context": {"platform": "web"}
}

try:
    response = requests.post(
        f"{BACKEND_URL}/api/assistant",
        headers={"Content-Type": "application/json", "X-API-Key": API_KEY},
        json=whatsapp_request,
        timeout=60
    )
    
    result = response.json()
    task = result.get("result", {}).get("task", {})
    execution = task.get("execution", {})
    
    print(f"Status: {response.status_code}")
    print(f"Execution Status: {execution.get('status', 'not_executed')}")
    print(f"Response: {result.get('result', {}).get('response')}")
    
    if execution.get('status') == 'success':
        print("\n✅ WHATSAPP WORKING ON PRODUCTION!")
        print(f"Message SID: {execution.get('message_sid')}")
    else:
        print(f"\n❌ WhatsApp failed: {execution.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("PRODUCTION TEST COMPLETE")
print("=" * 70)
print("\nCheck:")
print("1. Email inbox: blackholeinfiverse20@gmail.com")
print("2. WhatsApp: +919004484490")
print("=" * 70)
