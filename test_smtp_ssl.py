"""Quick test of the updated email executor with SMTP SSL."""
import os, sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.executors.email_executor import EmailExecutor

executor = EmailExecutor()

print("=" * 60)
print("TESTING SMTP SSL (port 465)")
print("=" * 60)
print(f"User: {executor.email_user}")
print(f"Pass set: {bool(executor.email_password)}")

# Test SMTP SSL directly
result = executor.send_email_smtp_ssl(
    to_email="rajprajapati8286@gmail.com",
    subject="SMTP SSL Test from AI Assistant",
    message="This email was sent via Gmail SMTP SSL (port 465). If you receive this, the fix is working!",
    trace_id="test_smtp_ssl_001"
)
print(f"\nSMTP SSL Result: {result}")

if result.get("status") == "success":
    print("\n[SUCCESS] SMTP SSL works! Email should arrive shortly.")
else:
    print(f"\n[FAILED] SMTP SSL failed: {result.get('error')}")
    
    # Also test full send_message which tries all methods
    print("\n--- Testing full send_message() ---")
    result2 = executor.send_message(
        to_email="rajprajapati8286@gmail.com",
        subject="Full Test from AI Assistant",
        message="This email tests the full fallback chain.",
        trace_id="test_full_002"
    )
    print(f"Full Result: {result2}")

print("\n" + "=" * 60)
