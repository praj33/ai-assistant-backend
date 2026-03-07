"""
Telegram Executor — Chandresh Integration
Sends and receives Telegram messages via Telegram Bot API.
All actions pass through Safety → Enforcement → Orchestration → Execution.
Supports simulation mode when TELEGRAM_BOT_TOKEN is not configured.
"""

import os
import requests
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TelegramExecutor:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    def send_message(self, to_chat_id: str, message: str, trace_id: str) -> Dict[str, Any]:
        """Send a message via Telegram Bot API."""
        try:
            if not self.bot_token:
                # Simulation mode — token not configured yet
                logger.info(f"[{trace_id}] Telegram simulation: sending to {to_chat_id}")
                return {
                    "status": "success",
                    "to": to_chat_id,
                    "message": message,
                    "method": "telegram_simulation",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "telegram",
                    "note": "Simulation mode — set TELEGRAM_BOT_TOKEN for live execution"
                }

            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": to_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }

            logger.info(f"[{trace_id}] Sending Telegram message to {to_chat_id}")
            response = requests.post(url, json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "message_id": result.get("result", {}).get("message_id"),
                    "to": to_chat_id,
                    "message": message,
                    "method": "telegram_bot_api",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "telegram"
                }
            else:
                error_detail = response.json().get("description", response.text)
                logger.error(f"[{trace_id}] Telegram API error: {response.status_code} - {error_detail}")
                return {
                    "status": "error",
                    "error": f"Telegram API error: {response.status_code} - {error_detail}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"[{trace_id}] Telegram execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }

    def receive_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """Parse incoming Telegram webhook update."""
        try:
            message = webhook_data.get("message", {})
            chat = message.get("chat", {})
            sender = message.get("from", {})

            return {
                "status": "received",
                "chat_id": str(chat.get("id", "")),
                "sender_id": str(sender.get("id", "")),
                "sender_name": sender.get("first_name", "") + " " + sender.get("last_name", ""),
                "username": sender.get("username", ""),
                "message": message.get("text", ""),
                "message_id": message.get("message_id"),
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "telegram"
            }
        except Exception as e:
            logger.error(f"Telegram webhook parsing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def set_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Register webhook URL with Telegram."""
        if not self.bot_token:
            return {"status": "error", "error": "Bot token not configured"}

        try:
            url = f"{self.base_url}/setWebhook"
            response = requests.post(url, json={"url": webhook_url}, timeout=30)
            result = response.json()
            return {
                "status": "success" if result.get("ok") else "error",
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
