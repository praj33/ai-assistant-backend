"""Debug script to find exactly where email sending fails."""
import os, sys, re
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

print("=" * 60)
print("EMAIL DEBUG DIAGNOSTIC")
print("=" * 60)

# 1. Check env vars
print("\n--- ENV VARS ---")
for k in ["EMAIL_USER", "EMAIL_PASSWORD", "SMTP_SERVER", "SMTP_PORT", "SENDGRID_API_KEY", "SENDGRID_FROM_EMAIL"]:
    v = os.getenv(k)
    if v:
        print(f"  {k} = {v[:6]}...{v[-4:]}" if len(v) > 10 else f"  {k} = {v}")
    else:
        print(f"  {k} = NOT SET")

# 2. Test regex parsing
print("\n--- REGEX PARSING ---")
test_messages = [
    'Send an email to rajprajapati8286@gmail.com with subject "AI Assistant Demo" saying "This is a live demo"',
    "send email to test@gmail.com",
    "email test@gmail.com saying hello world",
    'Send email to user@example.com with subject "Test" message "Hello"',
]

for text in test_messages:
    email_match = re.search(r'(?:to|send.*?to)\s+([\w\.-]+@[\w\.-]+)', text, re.IGNORECASE)
    subject_match = re.search(r"(?:subject|with subject)\s+['\"](.+?)['\"]", text, re.IGNORECASE)
    message_match = re.search(r"(?:message|saying|body)\s+['\"](.+?)['\"]", text, re.IGNORECASE)
    
    print(f"\n  Input: {text[:70]}...")
    print(f"  Email:   {email_match.group(1) if email_match else 'NOT FOUND'}")
    print(f"  Subject: {subject_match.group(1) if subject_match else 'NOT FOUND'}")
    print(f"  Message: {message_match.group(1) if message_match else 'NOT FOUND'}")
    
    if email_match:
        result = {
            "to": email_match.group(1),
            "subject": subject_match.group(1) if subject_match else "Message from AI Assistant",
            "message": message_match.group(1) if message_match else text
        }
        print(f"  -> Would pass to executor: {result}")
    else:
        print(f"  -> WOULD FAIL: 'Could not extract email parameters'")

# 3. Test actual executor
print("\n--- EXECUTOR TEST ---")
from app.services.execution_service import ExecutionService
gateway = ExecutionService()

print("  Gateway status OK:", gateway.get_status().get("status"))

# 4. Test email send through the universal gateway
print("\n--- GATEWAY EMAIL TEST (ALLOW) ---")
result = gateway.execute_action(
    action_type="email",
    action_data={
        "to": "blackholeinfiverse20@gmail.com",
        "subject": "Debug Full Test",
        "message": "Debug full test email (must pass gateway auth + enforcement).",
    },
    trace_id="debug_full_test",
    enforcement_decision="ALLOW",
)
print(f"  Gateway result: {result}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
