"""Quick test of the updated email executor with SMTP SSL."""
import os, sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.services.execution_service import ExecutionService

gateway = ExecutionService()

print("=" * 60)
print("TESTING SMTP SSL (port 465)")
print("=" * 60)
print("Using Universal Execution Gateway")

# Test email through gateway (will select best method internally)
result = gateway.execute_action(
    action_type="email",
    action_data={
        "to": "rajprajapati8286@gmail.com",
        "subject": "SMTP SSL Test from AI Assistant",
        "message": "This email was sent through the Universal Execution Gateway. If you receive this, email execution is working.",
    },
    trace_id="test_smtp_ssl_001",
    enforcement_decision="ALLOW",
)
print(f"\nSMTP SSL Result: {result}")

if result.get("status") == "success":
    print("\n[SUCCESS] SMTP SSL works! Email should arrive shortly.")
else:
    print(f"\n[FAILED] SMTP SSL failed: {result.get('error')}")
    
    # Also test full send_message which tries all methods
    print("\n--- Testing full send_message() ---")
    result2 = gateway.execute_action(
        action_type="email",
        action_data={
            "to": "rajprajapati8286@gmail.com",
            "subject": "Full Test from AI Assistant",
            "message": "This email tests the full fallback chain via gateway.",
        },
        trace_id="test_full_002",
        enforcement_decision="ALLOW",
    )
    print(f"Full Result: {result2}")

print("\n" + "=" * 60)
