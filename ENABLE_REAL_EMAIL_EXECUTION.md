# Enable Real Email Execution - Quick Setup Guide

## Option 1: Gmail SMTP (Easiest - 10 minutes)

### Step 1: Get Gmail App Password

1. Go to your Google Account: https://myaccount.google.com/
2. Click "Security" in left sidebar
3. Enable "2-Step Verification" if not already enabled
4. Search for "App passwords" or go to: https://myaccount.google.com/apppasswords
5. Select "Mail" and "Other (Custom name)"
6. Name it "AI Assistant"
7. Click "Generate"
8. **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

### Step 2: Update Backend .env File

Open `AI-ASSISTANT-/Backend/.env` and add:

```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your.email@gmail.com
EMAIL_PASSWORD=abcdefghijklmnop
```

**Replace:**
- `your.email@gmail.com` with your Gmail address
- `abcdefghijklmnop` with the app password (remove spaces)

### Step 3: Test Email Execution

```bash
cd AI-ASSISTANT-/Backend
python test_email_execution.py
```

---

## Option 2: SendGrid API (Production-Ready - 15 minutes)

### Step 1: Create SendGrid Account

1. Go to https://sendgrid.com/
2. Sign up for free account (100 emails/day free)
3. Verify your email address
4. Go to Settings → API Keys
5. Click "Create API Key"
6. Name it "AI Assistant"
7. Select "Full Access"
8. **Copy the API key** (starts with `SG.`)

### Step 2: Update Backend Code

Create `AI-ASSISTANT-/Backend/app/executors/sendgrid_executor.py`:

```python
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime

class SendGridExecutor:
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL")
    
    def send_message(self, to_email: str, subject: str, message: str, trace_id: str):
        if not self.api_key:
            return {"status": "error", "error": "SendGrid API key not configured"}
        
        try:
            mail = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=message
            )
            
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(mail)
            
            return {
                "status": "success",
                "to": to_email,
                "subject": subject,
                "message": message,
                "method": "sendgrid",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "email"
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "trace_id": trace_id}
```

### Step 3: Update .env

```bash
# SendGrid Configuration
SENDGRID_API_KEY=SG.your_api_key_here
SENDGRID_FROM_EMAIL=your.email@gmail.com
```

### Step 4: Install SendGrid

```bash
pip install sendgrid
```

---

## Quick Test Script

Create `AI-ASSISTANT-/Backend/test_email_execution.py`:

```python
import os
from dotenv import load_dotenv
from app.executors.email_executor import EmailExecutor

load_dotenv()

executor = EmailExecutor()

result = executor.send_message(
    to_email="your.test.email@gmail.com",  # Change this
    subject="AI Assistant Test Email",
    message="This is a test email from AI Assistant. If you receive this, email execution is working!",
    trace_id="test_trace_001"
)

print("Result:", result)

if result.get("status") == "success":
    print("✅ Email sent successfully!")
else:
    print("❌ Email failed:", result.get("error"))
```

Run:
```bash
python test_email_execution.py
```

---

## Verification Checklist

- [ ] Gmail app password generated
- [ ] `.env` file updated with credentials
- [ ] Test script runs successfully
- [ ] Test email received in inbox
- [ ] Backend restarted with new credentials

---

## Security Notes

1. **Never commit `.env` file to Git**
2. **Use app passwords, not your real Gmail password**
3. **For production, use SendGrid or AWS SES**
4. **Rotate credentials regularly**

---

## Troubleshooting

### "SMTP credentials not configured"
- Check `.env` file has `EMAIL_USER` and `EMAIL_PASSWORD`
- Restart backend after updating `.env`

### "Authentication failed"
- Verify app password is correct (no spaces)
- Ensure 2-Step Verification is enabled on Gmail
- Try regenerating app password

### "Connection refused"
- Check firewall/antivirus blocking port 587
- Try port 465 with SSL instead

---

## Next Steps

Once email is working:
1. Test via `/api/assistant` endpoint
2. Capture trace chain JSON
3. Record demo video
4. Document live execution proof
