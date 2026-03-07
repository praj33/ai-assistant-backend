"""Test the full API endpoint for email sending."""
import os, sys, json
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

import asyncio

# Simulate the full orchestrator flow without the HTTP layer
from app.core.assistant_orchestrator import handle_assistant_request, extract_action_parameters

# Test 1: Check parameter extraction
print("=" * 60)
print("TEST 1: Parameter extraction")
print("=" * 60)

test_inputs = [
    'Send an email to rajprajapati8286@gmail.com with subject "AI Assistant Demo" saying "This is a live demo"',
    'send email to blackholeinfiverse20@gmail.com saying "hello there"',
    'email blackholeinfiverse20@gmail.com',
    'send an email to blackholeinfiverse20@gmail.com',
]

for text in test_inputs:
    result = extract_action_parameters(text, "email")
    print(f"\n  Input:  {text[:70]}...")
    print(f"  Result: {result}")

# Test 2: Simulate a full request
print("\n" + "=" * 60)
print("TEST 2: Full orchestrator request")
print("=" * 60)

class FakeInput:
    def __init__(self, message):
        self.message = message
        self.summarized_payload = None
        self.audio_data = None

class FakeContext:
    def __init__(self):
        self.platform = "web"
        self.session_id = "debug_session"
        self.detected_language = None
        self.preferred_language = "en"
        self.audio_output_requested = False
        self.voice_input = False
    
    def dict(self):
        return {"platform": self.platform, "session_id": self.session_id}

class FakeRequest:
    def __init__(self, message):
        self.input = FakeInput(message)
        self.context = FakeContext()

async def test_full_flow():
    test_message = 'Send an email to blackholeinfiverse20@gmail.com with subject "Test Email" saying "Hello from debug test"'
    print(f"\n  Sending: {test_message[:70]}...")
    
    request = FakeRequest(test_message)
    result = await handle_assistant_request(request)
    
    print(f"\n  Status:     {result.get('status')}")
    print(f"  Trace ID:   {result.get('trace_id')}")
    print(f"  Type:       {result.get('result', {}).get('type')}")
    print(f"  Response:   {result.get('result', {}).get('response')}")
    
    execution = result.get('result', {}).get('execution')
    print(f"  Execution:  {execution}")
    
    enforcement = result.get('result', {}).get('enforcement', {})
    print(f"  Enforcement decision: {enforcement.get('decision')}")
    
    safety = result.get('result', {}).get('safety', {})
    print(f"  Safety decision: {safety.get('decision')}")
    
    if result.get('status') == 'error':
        print(f"\n  ERROR: {result.get('error')}")
    
    # Write full response for inspection
    with open("debug_api_email_response.json", "w") as f:
        json.dump(result, f, indent=2, default=str)
    print("\n  Full response saved to: debug_api_email_response.json")

asyncio.run(test_full_flow())

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
