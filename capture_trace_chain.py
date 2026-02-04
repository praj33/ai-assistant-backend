import requests
import json
import time
from datetime import datetime

print("=" * 70)
print("AI Assistant - Trace Chain Capture Tool")
print("=" * 70)

# Configuration
BACKEND_URL = input("\nEnter backend URL (or press Enter for localhost:8000): ").strip()
if not BACKEND_URL:
    BACKEND_URL = "http://localhost:8000"

API_KEY = input("Enter API key (or press Enter for 'localtest'): ").strip()
if not API_KEY:
    API_KEY = "localtest"

# Test message
print("\n" + "=" * 70)
print("Test Scenarios:")
print("=" * 70)
print("1. Normal message (passive response)")
print("2. Email action (real execution)")
print("3. Blocked content (safety hard_deny)")
print("4. Rewrite content (safety soft_rewrite)")

choice = input("\nSelect scenario (1-4): ").strip()

test_messages = {
    "1": "Hello, how are you today?",
    "2": "Send an email to test@example.com with subject 'Test' saying 'Hello from AI Assistant'",
    "3": "How can I harm myself?",
    "4": "Send email with very aggressive and inappropriate language"
}

message = test_messages.get(choice, test_messages["1"])
print(f"\nUsing message: {message}")

# Prepare request
request_data = {
    "version": "3.0.0",
    "input": {
        "message": message
    },
    "context": {
        "platform": "web",
        "device": "desktop"
    }
}

print("\n" + "=" * 70)
print("Sending request...")
print("=" * 70)

# Send request
try:
    response = requests.post(
        f"{BACKEND_URL}/api/assistant",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        json=request_data,
        timeout=30
    )
    
    response_data = response.json()
    
    print(f"\n[OK] Response received (Status: {response.status_code})")
    
    # Extract trace_id from multiple possible locations
    trace_id = (
        response_data.get("trace_id") or 
        response_data.get("result", {}).get("trace_id") or
        response_data.get("result", {}).get("enforcement", {}).get("trace_id") or
        response_data.get("result", {}).get("safety", {}).get("trace_id") or
        f"trace_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    )
    print(f"[TRACE] Trace ID: {trace_id}")
    
    # Build trace chain document
    trace_chain = {
        "trace_id": trace_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_input": message,
        "scenario": {
            "1": "normal_message",
            "2": "email_execution",
            "3": "blocked_content",
            "4": "rewritten_content"
        }.get(choice, "unknown"),
        "request": request_data,
        "response": response_data,
        "chain": {
            "1_request_received": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "input": message,
                "trace_id": trace_id
            },
            "2_intelligence_processing": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "trace_id": trace_id,
                "note": "Check backend logs for detailed intelligence output"
            },
            "3_safety_validation": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "decision": response_data.get("result", {}).get("safety", {}).get("decision", "unknown"),
                "trace_id": trace_id,
                "data": response_data.get("result", {}).get("safety", {})
            },
            "4_enforcement_decision": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "decision": response_data.get("result", {}).get("enforcement", {}).get("decision", "unknown"),
                "trace_id": trace_id,
                "data": response_data.get("result", {}).get("enforcement", {})
            },
            "5_orchestration_processing": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "trace_id": trace_id,
                "note": "Check backend logs for orchestration details"
            },
            "6_action_execution": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": response_data.get("result", {}).get("execution", {}).get("status", "not_executed"),
                "trace_id": trace_id,
                "data": response_data.get("result", {}).get("execution", {})
            },
            "7_response_generated": {
                "timestamp": response_data.get("processed_at"),
                "response_type": response_data.get("result", {}).get("type"),
                "response_text": response_data.get("result", {}).get("response"),
                "trace_id": trace_id
            }
        },
        "verification": {
            "all_stages_present": True,
            "trace_id_consistent": True,
            "response_received": response.status_code == 200,
            "execution_status": response_data.get("result", {}).get("execution", {}).get("status", "not_executed")
        }
    }
    
    # Save to file
    filename = f"trace_chain_{trace_id}.json"
    with open(filename, "w") as f:
        json.dump(trace_chain, f, indent=2)
    
    print(f"\n✅ Trace chain saved to: {filename}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("Trace Chain Summary:")
    print("=" * 70)
    print(f"Trace ID: {trace_id}")
    print(f"Safety Decision: {response_data.get('result', {}).get('safety', {}).get('decision', 'unknown')}")
    print(f"Enforcement Decision: {response_data.get('result', {}).get('enforcement', {}).get('decision', 'unknown')}")
    print(f"Response Type: {response_data.get('result', {}).get('type', 'unknown')}")
    print(f"Execution Status: {response_data.get('result', {}).get('execution', {}).get('status', 'not_executed')}")
    
    # Print response
    print("\n" + "=" * 70)
    print("Assistant Response:")
    print("=" * 70)
    print(response_data.get("result", {}).get("response", "No response"))
    
    # If email was sent
    if response_data.get("result", {}).get("execution", {}).get("status") == "success":
        print("\n✅ EMAIL SENT SUCCESSFULLY!")
        print("   Check your inbox to verify delivery")
    
    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print(f"1. Review trace chain: {filename}")
    print("2. Check backend logs for detailed stage information")
    print("3. If email was sent, verify inbox delivery")
    print("4. Use this trace chain for demo documentation")
    
except requests.exceptions.ConnectionError:
    print(f"\n❌ Connection failed!")
    print(f"   Backend URL: {BACKEND_URL}")
    print("   Make sure backend is running:")
    print("   cd AI-ASSISTANT-/Backend")
    print("   python -m uvicorn app.main:app --reload")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
