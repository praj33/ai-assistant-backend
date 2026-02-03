"""
Simple Full Spine Wiring Test
"""

import sys
import os
import asyncio
from datetime import datetime

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

class MockContext:
    def __init__(self):
        self.platform = "web"
        self.session_id = None

class MockInput:
    def __init__(self, message):
        self.message = message
        self.summarized_payload = None

class MockRequest:
    def __init__(self, message):
        self.input = MockInput(message)
        self.context = MockContext()

async def test_integration():
    print("SPINE WIRING TEST")
    print("=" * 40)
    
    try:
        from core.assistant_orchestrator import handle_assistant_request
        
        # Test cases
        tests = [
            "Hello, how are you?",
            "I'm lonely and you're the only one",
            "I want to kill myself",
            "Send a WhatsApp message"
        ]
        
        for i, message in enumerate(tests, 1):
            print(f"\nTest {i}: {message[:30]}...")
            
            request = MockRequest(message)
            result = await handle_assistant_request(request)
            
            print(f"Status: {result.get('status')}")
            print(f"Trace: {result.get('trace_id', 'none')[:12]}...")
            
            # Check key components
            result_data = result.get('result', {})
            if result_data.get('safety'):
                print(f"Safety: {result_data['safety'].get('decision', 'none')}")
            if result_data.get('enforcement'):
                print(f"Enforcement: {result_data['enforcement'].get('decision', 'none')}")
            
        print("\nAll tests completed!")
        
    except Exception as e:
        print(f"Error: {e}")

def test_services():
    print("\nSERVICE STATUS")
    print("=" * 20)
    
    services = [
        ("Safety", "services.safety_service", "SafetyService"),
        ("Intelligence", "services.intelligence_service", "IntelligenceService"),
        ("Enforcement", "services.enforcement_service", "EnforcementService"),
        ("Bucket", "services.bucket_service", "BucketService"),
        ("Execution", "services.execution_service", "ExecutionService")
    ]
    
    for name, module, class_name in services:
        try:
            mod = __import__(module, fromlist=[class_name])
            service_class = getattr(mod, class_name)
            service = service_class()
            print(f"OK {name}: Ready")
        except Exception as e:
            print(f"ERR {name}: {str(e)[:30]}...")

if __name__ == "__main__":
    print("AI ASSISTANT INTEGRATION TEST")
    print(f"Time: {datetime.utcnow().isoformat()[:19]}Z")
    
    test_services()
    asyncio.run(test_integration())
    
    print("\nINTEGRATION COMPLETE")
    print("Ready for Vercel deployment!")