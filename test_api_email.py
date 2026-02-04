import requests
import json
from datetime import datetime

print("=" * 70)
print("Email Execution Test via /api/assistant")
print("=" * 70)

# Test email execution
request_data = {
    "version": "3.0.0",
    "input": {
        "message": "Send an email to rajprajapati8286@gmail.com with subject 'AI Assistant Demo' saying 'This is a live demo of real email execution from AI Assistant!'"
    },
    "context": {
        "platform": "web",
        "device": "desktop"
    }
}

print("\nSending request to backend...")
print(f"Message: {request_data['input']['message'][:80]}...")

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
    
    print(f"\n[OK] Response Status: {response.status_code}")
    
    result = response.json()
    
    # Save full response
    with open("email_execution_response.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print("\n" + "=" * 70)
    print("RESPONSE DETAILS:")
    print("=" * 70)
    
    # Extract key information
    trace_id = result.get("trace_id", "N/A")
    response_text = result.get("result", {}).get("response", "N/A")
    response_type = result.get("result", {}).get("type", "N/A")
    
    # Safety info
    safety = result.get("result", {}).get("safety", {})
    safety_decision = safety.get("decision", "N/A")
    
    # Enforcement info
    enforcement = result.get("result", {}).get("enforcement", {})
    enforcement_decision = enforcement.get("decision", "N/A")
    
    # Execution info
    execution = result.get("result", {}).get("execution", {})
    task = result.get("result", {}).get("task", {})
    
    # Check both locations for execution status
    execution_status = (
        execution.get("status") or 
        task.get("execution", {}).get("status") or
        "not_executed"
    )
    
    print(f"\nTrace ID: {trace_id}")
    print(f"Response Type: {response_type}")
    print(f"Safety Decision: {safety_decision}")
    print(f"Enforcement Decision: {enforcement_decision}")
    print(f"Execution Status: {execution_status}")
    
    print(f"\nAssistant Response:")
    print(f"  {response_text}")
    
    if execution_status == "success":
        print("\n" + "=" * 70)
        print("[SUCCESS] EMAIL SENT!")
        print("=" * 70)
        print("\nCheck inbox: rajprajapati8286@gmail.com")
        print("Subject: AI Assistant Demo")
        print("\nFull response saved to: email_execution_response.json")
    elif execution_status == "error":
        print(f"\n[ERROR] Execution failed: {execution.get('error')}")
    else:
        print(f"\n[INFO] Execution status: {execution_status}")
    
    print("\n" + "=" * 70)
    
except requests.exceptions.ConnectionError:
    print("\n[ERROR] Cannot connect to backend!")
    print("Make sure backend is running:")
    print("  cd AI-ASSISTANT-/Backend")
    print("  python -m uvicorn app.main:app --reload")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
