import requests
import json

print("=" * 70)
print("WhatsApp Execution Test via /api/assistant")
print("=" * 70)

request_data = {
    "version": "3.0.0",
    "input": {
        "message": "Send WhatsApp to +919136919017 saying 'This is a live demo of WhatsApp execution from AI Assistant!'"
    },
    "context": {
        "platform": "web",
        "device": "desktop"
    }
}

print("\nSending request to backend...")
print(f"Message: {request_data['input']['message']}")

try:
    response = requests.post(
        "http://localhost:8000/api/assistant",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "localtest"
        },
        json=request_data,
        timeout=30
    )
    
    result = response.json()
    
    with open("whatsapp_execution_response.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n[OK] Response Status: {response.status_code}")
    
    print("\n" + "=" * 70)
    print("RESPONSE DETAILS:")
    print("=" * 70)
    
    trace_id = result.get("trace_id", "N/A")
    response_text = result.get("result", {}).get("response", "N/A")
    response_type = result.get("result", {}).get("type", "N/A")
    
    safety = result.get("result", {}).get("safety", {})
    safety_decision = safety.get("decision", "N/A")
    
    enforcement = result.get("result", {}).get("enforcement", {})
    enforcement_decision = enforcement.get("decision", "N/A")
    
    task = result.get("result", {}).get("task", {})
    execution = task.get("execution", {})
    execution_status = execution.get("status", "not_executed")
    
    print(f"\nTrace ID: {trace_id}")
    print(f"Response Type: {response_type}")
    print(f"Safety Decision: {safety_decision}")
    print(f"Enforcement Decision: {enforcement_decision}")
    print(f"Execution Status: {execution_status}")
    
    print(f"\nAssistant Response:")
    print(f"  {response_text}")
    
    if execution_status == "success":
        print("\n" + "=" * 70)
        print("[SUCCESS] WHATSAPP MESSAGE SENT!")
        print("=" * 70)
        print(f"\nTo: {execution.get('to')}")
        print(f"Message SID: {execution.get('message_sid')}")
        print("\nCheck WhatsApp: +919136919017")
        print("\nFull response saved to: whatsapp_execution_response.json")
    elif execution_status == "error":
        print(f"\n[ERROR] Execution failed: {execution.get('error')}")
    else:
        print(f"\n[INFO] Execution status: {execution_status}")
    
    print("\n" + "=" * 70)
    
except requests.exceptions.ConnectionError:
    print("\n[ERROR] Cannot connect to backend!")
    print("Make sure backend is running:")
    print("  python -m uvicorn app.main:app --reload")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
