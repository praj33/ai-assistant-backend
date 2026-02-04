import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.executors.whatsapp_executor import WhatsAppExecutor

load_dotenv()

print("=" * 60)
print("AI Assistant - WhatsApp Execution Test")
print("=" * 60)

# Check credentials
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

if not account_sid or not auth_token:
    print("\n[X] Twilio credentials not configured!")
    print("\nPlease update your .env file with:")
    print("  TWILIO_ACCOUNT_SID=ACxxxxxxxx")
    print("  TWILIO_AUTH_TOKEN=your_token")
    print("\nSee ENABLE_WHATSAPP_EXECUTION.md for setup.")
    sys.exit(1)

print(f"\n[OK] Twilio credentials found")
print(f"   Account SID: {account_sid[:10]}...")

# Get test number
test_number = input("\nEnter WhatsApp number (with country code, e.g., +919876543210): ").strip()

if not test_number:
    print("[ERROR] Phone number required")
    sys.exit(1)

print(f"\n[WHATSAPP] Sending test message to: {test_number}")
print("\nIMPORTANT: Recipient must join Twilio sandbox first!")
print("Send 'join <code>' to +1 415 523 8886 from WhatsApp")

# Initialize executor
executor = WhatsAppExecutor()

# Send test message
result = executor.send_message(
    to_number=test_number,
    message="This is a test message from AI Assistant. If you receive this, WhatsApp execution is working!",
    trace_id="test_trace_whatsapp_001"
)

print("\n" + "=" * 60)
print("Result:")
print("=" * 60)

if result.get("status") == "success":
    print("\n[SUCCESS] WHATSAPP MESSAGE SENT!")
    print(f"\n   To: {result.get('to')}")
    print(f"   Message SID: {result.get('message_sid')}")
    print(f"   Trace ID: {result.get('trace_id')}")
    print(f"   Timestamp: {result.get('timestamp')}")
    print("\n[OK] Check WhatsApp to confirm delivery!")
else:
    print("\n[FAILED] WHATSAPP FAILED!")
    print(f"\n   Error: {result.get('error')}")
    if "not configured" in result.get('error', ''):
        print("\n   Setup Twilio:")
        print("   1. Go to https://www.twilio.com/try-twilio")
        print("   2. Get Account SID and Auth Token")
        print("   3. Update .env file")
    elif "sandbox" in result.get('error', '').lower():
        print("\n   Recipient must join sandbox:")
        print("   Send 'join <code>' to +1 415 523 8886")
    print("\n   See ENABLE_WHATSAPP_EXECUTION.md for help")

print("\n" + "=" * 60)
