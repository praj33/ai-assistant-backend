import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Message Delivery Verification")
print("=" * 60)

# Check Email
print("\n[EMAIL]")
print(f"From: {os.getenv('EMAIL_USER')}")
print(f"To: rajprajapati8286@gmail.com")
print(f"Subject: AI Assistant Demo")
print("\nCheck:")
print("1. Inbox of rajprajapati8286@gmail.com")
print("2. Spam/Junk folder")
print("3. All Mail folder")

# Check WhatsApp
print("\n[WHATSAPP]")
print(f"From: {os.getenv('TWILIO_WHATSAPP_NUMBER')}")
print(f"To: +919136919017")
print(f"Message SID: SM12caab10028cf64518eab0ea6b10564e")

print("\nIMPORTANT: Did you join Twilio sandbox?")
print("You must send this from WhatsApp +919136919017:")
print("  'join <code>' to +1 415 523 8886")
print("\nTo find your code:")
print("  https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")

print("\n" + "=" * 60)
print("Which message didn't you receive?")
print("1. Email")
print("2. WhatsApp")
print("3. Both")
choice = input("\nEnter 1, 2, or 3: ").strip()

if choice == "1":
    print("\n[EMAIL TROUBLESHOOTING]")
    print("1. Check spam folder")
    print("2. Search for 'AI Assistant Demo'")
    print("3. Check 'All Mail' folder")
    print("4. Verify email: rajprajapati8286@gmail.com")
    
elif choice == "2":
    print("\n[WHATSAPP TROUBLESHOOTING]")
    print("1. Did you join sandbox? Send 'join <code>' to +1 415 523 8886")
    print("2. Check WhatsApp on +919136919017")
    print("3. Look for message from +1 415 523 8886")
    print("4. Check if number is correct")
    
elif choice == "3":
    print("\n[BOTH NOT RECEIVED]")
    print("Let's test again with your number:")
    
    test_email = input("\nEnter your email to test: ").strip()
    test_phone = input("Enter your WhatsApp number (with +91): ").strip()
    
    print(f"\nWe'll send test messages to:")
    print(f"  Email: {test_email}")
    print(f"  WhatsApp: {test_phone}")
    print("\nRun these commands:")
    print(f"  python test_email_execution.py  # Enter: {test_email}")
    print(f"  python test_whatsapp_execution.py  # Enter: {test_phone}")

print("\n" + "=" * 60)
