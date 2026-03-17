import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.core.gateway_auth import GatewayAuthError, require_gateway_invocation

logger = logging.getLogger(__name__)

class WhatsAppExecutor:
    def __init__(self):
        # Provider selection (default: twilio for backwards compatibility)
        # Supported: twilio | cloud (Meta WhatsApp Cloud API)
        provider_env = (os.getenv("WHATSAPP_PROVIDER") or "").strip().lower()
        if provider_env:
            self.provider = provider_env
        elif os.getenv("WHATSAPP_CLOUD_ACCESS_TOKEN") and os.getenv("WHATSAPP_CLOUD_PHONE_NUMBER_ID"):
            self.provider = "cloud"
        else:
            self.provider = "twilio"

        # --- Twilio WhatsApp ---
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        self.twilio_base_url = (
            f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            if self.account_sid
            else None
        )

        # --- WhatsApp Cloud API (Meta Graph) ---
        self.cloud_access_token = os.getenv("WHATSAPP_CLOUD_ACCESS_TOKEN")
        self.cloud_phone_number_id = os.getenv("WHATSAPP_CLOUD_PHONE_NUMBER_ID")
        self.cloud_api_version = (os.getenv("WHATSAPP_CLOUD_API_VERSION") or "v20.0").strip()
        self.cloud_base_url = (os.getenv("WHATSAPP_CLOUD_BASE_URL") or "https://graph.facebook.com").strip()

    @staticmethod
    def _normalize_e164(value: str) -> str:
        # Cloud API expects digits only (no "whatsapp:" prefix). We'll keep '+' if present then strip.
        raw = (value or "").strip()
        if raw.lower().startswith("whatsapp:"):
            raw = raw.split(":", 1)[1].strip()
        raw = raw.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        # Remove leading '+', Cloud API accepts without it; we will send digits only.
        if raw.startswith("+"):
            raw = raw[1:]
        return raw

    def _send_via_twilio(self, *, to_number: str, message: str, trace_id: str) -> Dict[str, Any]:
        if not self.account_sid or not self.auth_token:
            return {
                "status": "error",
                "error": "Twilio credentials not configured",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "whatsapp",
                "provider": "twilio",
            }

        if not self.twilio_base_url:
            return {
                "status": "error",
                "error": "Twilio base URL not configured",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "whatsapp",
                "provider": "twilio",
            }

        # Format phone number for Twilio WhatsApp
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"

        data = {
            "From": self.whatsapp_number,
            "To": to_number,
            "Body": message,
        }

        response = requests.post(
            self.twilio_base_url,
            data=data,
            auth=(self.account_sid, self.auth_token),
            timeout=30,
        )

        if response.status_code == 201:
            result = response.json()
            return {
                "status": "success",
                "message_sid": result.get("sid"),
                "to": to_number,
                "message": message,
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "whatsapp",
                "provider": "twilio",
            }

        return {
            "status": "error",
            "error": f"Twilio API error: {response.status_code}",
            "details": response.text,
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "whatsapp",
            "provider": "twilio",
        }

    def _send_via_cloud(self, *, to_number: str, message: str, trace_id: str) -> Dict[str, Any]:
        if not self.cloud_access_token or not self.cloud_phone_number_id:
            return {
                "status": "error",
                "error": "WhatsApp Cloud credentials not configured",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "whatsapp",
                "provider": "cloud",
            }

        to_digits = self._normalize_e164(to_number)
        if not to_digits:
            return {
                "status": "error",
                "error": "Recipient number is missing",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "whatsapp",
                "provider": "cloud",
            }

        url = f"{self.cloud_base_url.rstrip('/')}/{self.cloud_api_version}/{self.cloud_phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.cloud_access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_digits,
            "type": "text",
            "text": {"body": message},
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code in {200, 201}:
            result = response.json()
            message_id = None
            if isinstance(result, dict):
                messages = result.get("messages")
                if isinstance(messages, list) and messages:
                    message_id = messages[0].get("id")

            return {
                "status": "success",
                "message_id": message_id,
                "to": to_digits,
                "message": message,
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "whatsapp",
                "provider": "cloud",
                "raw": result,
            }

        return {
            "status": "error",
            "error": f"WhatsApp Cloud API error: {response.status_code}",
            "details": response.text,
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "whatsapp",
            "provider": "cloud",
        }
        
    def send_message(self, to_number: str, message: str, trace_id: str, gateway_auth: str = None) -> Dict[str, Any]:
        """Send WhatsApp message via the selected provider (Twilio or Cloud API)."""
        try:
            try:
                require_gateway_invocation(
                    gateway_auth=gateway_auth,
                    trace_id=trace_id,
                    platform="whatsapp",
                    action="send_message",
                )
            except GatewayAuthError as e:
                return {
                    "status": "error",
                    "error": f"unauthorized: {str(e)}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "whatsapp",
                }

            if self.provider == "cloud":
                return self._send_via_cloud(to_number=to_number, message=message, trace_id=trace_id)
            if self.provider == "twilio":
                return self._send_via_twilio(to_number=to_number, message=message, trace_id=trace_id)

            return {
                "status": "error",
                "error": f"Unknown WhatsApp provider: {self.provider}. Use WHATSAPP_PROVIDER=twilio|cloud.",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "whatsapp",
            }
                
        except Exception as e:
            logger.error(f"WhatsApp execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def receive_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """Handle incoming WhatsApp webhook"""
        return {
            "status": "received",
            "from": webhook_data.get("From"),
            "body": webhook_data.get("Body"),
            "message_sid": webhook_data.get("MessageSid"),
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "whatsapp"
        }
