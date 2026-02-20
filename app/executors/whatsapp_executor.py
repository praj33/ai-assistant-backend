import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WhatsAppExecutor:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        
    def send_message(self, to_number: str, message: str, trace_id: str) -> Dict[str, Any]:
        """Send WhatsApp message via Twilio"""
        try:
            if not self.account_sid or not self.auth_token:
                return {
                    "status": "error",
                    "error": "Twilio credentials not configured",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Format phone number for WhatsApp
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
            
            data = {
                "From": self.whatsapp_number,
                "To": to_number,
                "Body": message
            }
            
            response = requests.post(
                self.base_url,
                data=data,
                auth=(self.account_sid, self.auth_token),
                timeout=30
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
                    "platform": "whatsapp"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Twilio API error: {response.status_code}",
                    "details": response.text,
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()
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