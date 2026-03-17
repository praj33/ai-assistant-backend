# WhatsApp Cloud API Setup

This project supports WhatsApp Cloud API for outbound and inbound messages.
Use this checklist to configure Cloud API and wire webhooks.

## 1) Environment variables

Set these in `.env`:

```bash
# Force Cloud API
WHATSAPP_PROVIDER=cloud

# Cloud API credentials
WHATSAPP_CLOUD_ACCESS_TOKEN=your_access_token
WHATSAPP_CLOUD_PHONE_NUMBER_ID=your_phone_number_id

# Optional overrides
WHATSAPP_CLOUD_API_VERSION=v20.0
WHATSAPP_CLOUD_BASE_URL=https://graph.facebook.com

# Webhook verification and signatures
WHATSAPP_VERIFY_TOKEN=your_verify_token
WHATSAPP_WEBHOOK_SECRET=your_app_secret
```

Notes:
- `WHATSAPP_WEBHOOK_SECRET` should be your Meta App Secret (used to verify `X-Hub-Signature-256`).
- `WHATSAPP_VERIFY_TOKEN` is the token you set in the Meta webhook config UI.

## 2) Webhook URL

Configure your Meta webhook to point to:

```
{PUBLIC_BASE_URL}/webhook/whatsapp
```

You can use `/webhooks/whatsapp` as well. The app exposes both.

## 3) Test outbound

Run:

```bash
python test_whatsapp_execution.py
```

## 4) Test inbound

After webhook verification succeeds in the Meta UI, send a WhatsApp message
to the connected phone number. The webhook will forward the message into the
unified inbound gateway.
