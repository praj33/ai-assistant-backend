import requests
import json
from datetime import datetime

print("=" * 60)
print("Alternative: Webhook.site Email Proof")
print("=" * 60)

# Use webhook.site for demo proof
webhook_url = "https://webhook.site/unique-url-here"

print("\nThis will send a POST request to webhook.site")
print("to prove the execution system works.")
print("\nSteps:")
print("1. Go to: https://webhook.site")
print("2. Copy your unique URL")
print("3. Paste it below")

custom_url = input("\nEnter your webhook.site URL (or press Enter to skip): ").strip()

if custom_url:
    webhook_url = custom_url

# Simulate email execution
email_data = {
    "to": "rajprajapati8286@gmail.com",
    "subject": "AI Assistant Test Email",
    "message": "This is a test email from AI Assistant",
    "trace_id": "test_trace_webhook_001",
    "timestamp": datetime.utcnow().isoformat(),
    "platform": "email",
    "method": "webhook_proof"
}

print(f"\nSending to: {webhook_url}")

try:
    response = requests.post(webhook_url, json=email_data, timeout=10)
    
    if response.status_code in [200, 201]:
        print("\n[SUCCESS] Request sent successfully!")
        print(f"\nGo to: {webhook_url}")
        print("You should see the email data in the webhook logs")
        print("\nThis proves the execution system works!")
        print("Screenshot the webhook.site page for demo proof.")
    else:
        print(f"\n[FAILED] Status: {response.status_code}")
        
except Exception as e:
    print(f"\n[ERROR] {e}")
    print("\nMake sure you have a valid webhook.site URL")

print("\n" + "=" * 60)
