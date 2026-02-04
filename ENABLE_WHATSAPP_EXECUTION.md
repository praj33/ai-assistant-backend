# Enable WhatsApp Execution - Quick Setup

## Option 1: Twilio WhatsApp (Recommended - 10 minutes)

### Step 1: Create Twilio Account (5 min)

1. Go to: https://www.twilio.com/try-twilio
2. Sign up for free trial account
3. Verify your phone number
4. You'll get $15 free credit

### Step 2: Get Credentials (2 min)

1. Go to Twilio Console: https://console.twilio.com/
2. Find your **Account SID** (starts with AC...)
3. Find your **Auth Token** (click to reveal)
4. Copy both

### Step 3: Enable WhatsApp Sandbox (2 min)

1. In Twilio Console, go to: **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Or go directly to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
3. You'll see a sandbox number like: **+1 415 523 8886**
4. **Join the sandbox**: Send "join <code>" to that number from your WhatsApp
5. Example: Send "join <your-code>" to +1 415 523 8886

### Step 4: Update .env File (1 min)

Add to `AI-ASSISTANT-/Backend/.env`:

```bash
# WhatsApp Configuration (Twilio)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### Step 5: Test WhatsApp Execution

```bash
cd AI-ASSISTANT-/Backend
python test_whatsapp_execution.py
```

---

## Option 2: WhatsApp Business API (Production)

For production use, you need:
1. WhatsApp Business Account
2. Facebook Business Manager
3. Approved phone number
4. Takes 1-2 weeks for approval

**For demo, use Twilio Sandbox (Option 1)**

---

## Quick Test

After setup, test with:

```bash
python test_whatsapp_execution.py
```

Or via API:

```bash
curl -X POST http://localhost:8000/api/assistant \
  -H "Content-Type: application/json" \
  -H "X-API-Key: localtest" \
  -d '{
    "version": "3.0.0",
    "input": {
      "message": "Send WhatsApp to +919876543210 saying Hello from AI Assistant"
    },
    "context": {"platform": "web"}
  }'
```

---

## Important Notes

1. **Sandbox Limitations**:
   - Only works with numbers that joined the sandbox
   - Free for testing
   - Limited to 500 messages/day

2. **Phone Number Format**:
   - Include country code: +919876543210
   - Or: whatsapp:+919876543210

3. **Joining Sandbox**:
   - Each recipient must join the sandbox first
   - Send "join <code>" to Twilio's WhatsApp number
   - Code is shown in Twilio Console

---

## Troubleshooting

### "Credentials not configured"
- Check .env has TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
- Restart backend after updating .env

### "Recipient not in sandbox"
- Recipient must join sandbox first
- Send "join <code>" to +1 415 523 8886

### "Invalid phone number"
- Use format: +919876543210 (with country code)
- Or: whatsapp:+919876543210

---

## Next Steps

1. Create Twilio account
2. Get Account SID and Auth Token
3. Join WhatsApp sandbox
4. Update .env file
5. Test execution
