import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import base64
import json

logger = logging.getLogger(__name__)

class EmailExecutor:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.gmail_token = os.getenv("GMAIL_ACCESS_TOKEN")
        
    def send_email_smtp(self, to_email: str, subject: str, message: str, trace_id: str) -> Dict[str, Any]:
        """Send email via SMTP"""
        try:
            if not self.email_user or not self.email_password:
                return {
                    "status": "error",
                    "error": "SMTP credentials not configured",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            
            text = msg.as_string()
            server.sendmail(self.email_user, to_email, text)
            server.quit()
            
            return {
                "status": "success",
                "to": to_email,
                "subject": subject,
                "message": message,
                "method": "smtp",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "email"
            }
            
        except Exception as e:
            logger.error(f"SMTP email execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def send_email_gmail_api(self, to_email: str, subject: str, message: str, trace_id: str) -> Dict[str, Any]:
        """Send email via Gmail API"""
        try:
            if not self.gmail_token:
                return self.send_email_smtp(to_email, subject, message, trace_id)
            
            email_msg = MIMEText(message)
            email_msg['to'] = to_email
            email_msg['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(email_msg.as_bytes()).decode()
            
            headers = {
                'Authorization': f'Bearer {self.gmail_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'raw': raw_message
            }
            
            response = requests.post(
                'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "message_id": result.get("id"),
                    "to": to_email,
                    "subject": subject,
                    "message": message,
                    "method": "gmail_api",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "email"
                }
            else:
                return self.send_email_smtp(to_email, subject, message, trace_id)
                
        except Exception as e:
            logger.error(f"Gmail API execution failed, falling back to SMTP: {e}")
            return self.send_email_smtp(to_email, subject, message, trace_id)
    
    def send_message(self, to_email: str, subject: str, message: str, trace_id: str) -> Dict[str, Any]:
        """Main send method - tries Gmail API first, falls back to SMTP"""
        return self.send_email_gmail_api(to_email, subject, message, trace_id)