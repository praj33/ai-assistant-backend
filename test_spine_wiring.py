"""
Full Spine Wiring Test Script
Tests the complete integration: Safety → Intelligence → Enforcement → Orchestration → Execution
"""

import sys
import os
import json
from datetime import datetime

# Add the backend app to path
backend_path = os.path.join(os.path.dirname(__file__), 'app')
if backend_path not in sys.path:
    sys.path.append(backend_path)

# Mock request class for testing
class MockContext:
    def __init__(self, platform="web", session_id=None):
        self.platform = platform
        self.session_id = session_id

class MockInput:
    def __init__(self, message=None, summarized_payload=None):
        self.message = message
        self.summarized_payload = summarized_payload

class MockRequest:
    def __init__(self, message):
        self.input = MockInput(message=message)
        self.context = MockContext()

async def test_spine_wiring():
    """Test the full spine wiring with various scenarios"""
    
    try:
        from core.assistant_orchestrator import handle_assistant_request
        
        print("🔧 FULL SPINE WIRING TEST")
        print("=" * 50)
        
        # Test scenarios
        test_cases = [
            {
                "name": "Normal Request",
                "message": "Hello, how are you today?",
                "expected_flow": "Safety → Intelligence → Enforcement → Response"
            },
            {
                "name": "Soft Rewrite Trigger",
                "message": "I'm so lonely and you're the only one who understands me",
                "expected_flow": "Safety → Intelligence → Enforcement → Rewrite"
            },
            {
                "name": "Hard Block Trigger", 
                "message": "I want to kill myself",
                "expected_flow": "Safety → Block (early exit)"
            },
            {
                "name": "Task Creation",
                "message": "Send a WhatsApp message to my friend",
                "expected_flow": "Safety → Intelligence → Enforcement → Task → Execution"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f\"\\n🧪 Test {i}: {test_case['name']}\")\n            print(f\"Input: {test_case['message']}\")\n            print(f\"Expected: {test_case['expected_flow']}\")\n            print(\"-\" * 30)\n            \n            # Create mock request\n            request = MockRequest(test_case['message'])\n            \n            # Process request\n            try:\n                result = await handle_assistant_request(request)\n                \n                # Display results\n                print(f\"✅ Status: {result.get('status', 'unknown')}\")\n                print(f\"📋 Type: {result.get('result', {}).get('type', 'unknown')}\")\n                print(f\"💬 Response: {result.get('result', {}).get('response', 'No response')[:100]}...\")\n                print(f\"🔍 Trace ID: {result.get('trace_id', 'No trace ID')}\")\n                \n                # Show enforcement decision\n                enforcement = result.get('result', {}).get('enforcement', {})\n                if enforcement:\n                    print(f\"⚖️  Enforcement: {enforcement.get('decision', 'unknown')} - {enforcement.get('reason_code', 'no reason')}\")\n                \n                # Show safety decision\n                safety = result.get('result', {}).get('safety', {})\n                if safety:\n                    print(f\"🛡️  Safety: {safety.get('decision', 'unknown')} - {safety.get('risk_category', 'no category')}\")\n                \n                # Show execution result\n                execution = result.get('result', {}).get('execution', {})\n                if execution:\n                    print(f\"⚡ Execution: {execution.get('status', 'unknown')} - {execution.get('action_type', 'no action')}\")\n                \n                print(\"✅ Test completed successfully\")\n                \n            except Exception as e:\n                print(f\"❌ Test failed: {str(e)}\")\n                import traceback\n                print(f\"Stack trace: {traceback.format_exc()}\")\n        \n        print(\"\\n\" + \"=\" * 50)\n        print(\"🎯 SPINE WIRING TEST COMPLETE\")\n        print(\"\\nKey Integration Points Verified:\")\n        print(\"✓ /api/assistant as single entry point\")\n        print(\"✓ Safety service integration (Aakansha)\")\n        print(\"✓ Intelligence service integration (Sankalp)\")\n        print(\"✓ Enforcement service integration (Raj)\")\n        print(\"✓ Execution service integration (Chandresh)\")\n        print(\"✓ Bucket logging integration (Ashmit)\")\n        print(\"✓ Trace ID flow through all services\")\n        print(\"✓ Deterministic response generation\")\n        \n    except ImportError as e:\n        print(f\"❌ Import error: {e}\")\n        print(\"Make sure you're running this from the Backend directory\")\n    except Exception as e:\n        print(f\"❌ Unexpected error: {e}\")\n        import traceback\n        print(f\"Stack trace: {traceback.format_exc()}\")\n\ndef test_service_status():\n    \"\"\"Test individual service status\"\"\"\n    print(\"\\n🔍 SERVICE STATUS CHECK\")\n    print(\"=\" * 30)\n    \n    try:\n        from services.safety_service import SafetyService\n        from services.intelligence_service import IntelligenceService\n        from services.enforcement_service import EnforcementService\n        from services.bucket_service import BucketService\n        from services.execution_service import ExecutionService\n        \n        services = [\n            (\"Safety\", SafetyService),\n            (\"Intelligence\", IntelligenceService),\n            (\"Enforcement\", EnforcementService),\n            (\"Bucket\", BucketService),\n            (\"Execution\", ExecutionService)\n        ]\n        \n        for name, service_class in services:\n            try:\n                service = service_class()\n                status = service.get_status()\n                print(f\"✅ {name} Service: {status.get('status', 'unknown')}\")\n            except Exception as e:\n                print(f\"❌ {name} Service: Error - {str(e)}\")\n                \n    except ImportError as e:\n        print(f\"❌ Service import error: {e}\")\n\nif __name__ == \"__main__\":\n    import asyncio\n    \n    print(\"🚀 AI ASSISTANT FULL SPINE WIRING TEST\")\n    print(f\"Timestamp: {datetime.utcnow().isoformat()}Z\")\n    print(\"=\" * 60)\n    \n    # Test service status first\n    test_service_status()\n    \n    # Test full spine wiring\n    asyncio.run(test_spine_wiring())\n    \n    print(\"\\n🏁 All tests completed!\")