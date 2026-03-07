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
from app.executors.email_executor import EmailExecutor
executor = EmailExecutor()
print(f"  SMTP: {executor.smtp_server}:{executor.smtp_port}")
print(f"  User: {executor.email_user}")
print(f"  Pass set: {bool(executor.email_password)}")
print(f"  SendGrid key set: {bool(executor.sendgrid_key)}")

# 4. Test SendGrid specifically
if executor.sendgrid_key:
    print("\n--- SENDGRID TEST ---")
    result = executor.send_email_sendgrid(
        to_email="blackholeinfiverse20@gmail.com",
        subject="Debug Test",
        message="Debug test email",
        trace_id="debug_test"
    )
    print(f"  SendGrid result: {result}")

# 5. Test SMTP specifically
print("\n--- SMTP TEST ---")
result = executor.send_email_smtp(
    to_email="blackholeinfiverse20@gmail.com",
    subject="Debug Test SMTP",
    message="Debug test email via SMTP",
    trace_id="debug_smtp_test"
)
print(f"  SMTP result: {result}")

# 6. Test full send_message (which tries SendGrid -> Gmail API -> SMTP)
print("\n--- FULL send_message() TEST ---")
result = executor.send_message(
    to_email="blackholeinfiverse20@gmail.com",
    subject="Debug Full Test",
    message="Debug full test email",
    trace_id="debug_full_test"
)
print(f"  Full result: {result}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
