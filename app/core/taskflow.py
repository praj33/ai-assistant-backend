"""
TaskFlow Module - Sankalp's Cognitive Task Mapping Engine
Maps intents to task types with parameter extraction and priority computation.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
import re

class TaskFlow:
    def __init__(self):
        # Official intent to task type mapping
        self.INTENT_TO_TASK = {
            "create_reminder": "reminder",
            "set_alarm": "alarm",
            "schedule_meeting": "meeting",
            "send_email": "email",
            "search_web": "search",
            "create_note": "note",
            "get_weather": "weather",
            "manage_calendar": "calendar",
            "call_someone": "call",
            "music_control": "music",
            "navigate": "directions",
            "task_general": "general_task"
        }

    def extract_parameters(self, entities: Dict[str, Any], original_text: str = "") -> Dict[str, Any]:
        """Extract task parameters from entities."""
        params = {}

        # datetime - combine date and time
        if "date" in entities and entities["date"]:
            date_str = entities["date"][0] if isinstance(entities["date"], list) else entities["date"]
            datetime_str = date_str

            if "time" in entities and entities["time"]:
                time_str = entities["time"][0] if isinstance(entities["time"], list) else entities["time"]
                # Convert to ISO format
                try:
                    # Simple conversion - assume YYYY-MM-DD and HH:MM
                    datetime_str = f"{date_str}T{time_str}:00"
                except:
                    datetime_str = date_str

            params["datetime"] = datetime_str

        # message/content - use original text or look for content
        if original_text:
            params["message"] = original_text
        elif "text" in entities:
            params["message"] = entities["text"]

        # contact - from email or phone
        if "email" in entities and entities["email"]:
            params["contact"] = entities["email"][0] if isinstance(entities["email"], list) else entities["email"]
        elif "phone" in entities and entities["phone"]:
            params["contact"] = entities["phone"][0] if isinstance(entities["phone"], list) else entities["phone"]

        # location - if present
        if "location" in entities:
            params["location"] = entities["location"]

        # query - for search tasks
        if "query" in entities:
            params["query"] = entities["query"]

        return params

    def compute_priority(self, intent: str, entities: Dict[str, Any], context: Dict[str, Any], original_text: str = "") -> str:
        """Compute task priority based on rules."""
        text_lower = original_text.lower() if original_text else ""

        # High priority rules
        if "urgent" in text_lower or "asap" in text_lower:
            return "high"

        # Check if date is today
        if "date" in entities:
            try:
                date_str = entities["date"][0] if isinstance(entities["date"], list) else entities["date"]
                task_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                today = datetime.now().date()
                if task_date == today:
                    return "high"
            except:
                pass

        # Medium priority for meetings
        if intent == "schedule_meeting":
            return "medium"

        # Default from context or normal
        return context.get("priority", "normal")

    def build_task(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the final task object from intent data using PDF classification rules."""
        text = intent_data.get("text", "").lower()
        entities = intent_data.get("entities", {})
        dates_times = intent_data.get("dates_times", {})
        context = intent_data.get("context", {})

        # --- PDF Task Type Rules ---
        if "remind" in text or "reminder" in text:
            task_type = "reminder"
        elif "meeting" in text or "schedule" in text:
            task_type = "meeting"
        elif "call" in text:
            task_type = "call"
        elif "note" in text or "write this" in text:
            task_type = "note"
        elif "email" in text or "send mail" in text or "mailto:" in text:
            task_type = "email"
        elif "wake me" in text or "set alarm" in text:
            task_type = "alarm"
        elif "calendar" in text:
            task_type = "calendar"
        elif "whatsapp" in text or "send message" in text:
            task_type = "whatsapp"
        else:
            task_type = "general_task"

        # --- Parameters ---
        parameters = {
            "datetime": dates_times.get("resolved_date"),
            "message": entities.get("text"),
            "person": entities.get("person"),
            "location": entities.get("location")
        }

        parameters = {k: v for k, v in parameters.items() if v}

        # --- Final Task Object ---
        return {
            "task_type": task_type,
            "parameters": parameters,
            "priority": context.get("priority", "normal"),
            "confidence": intent_data.get("confidence", 0.85),
            "timestamp": datetime.utcnow().isoformat(),
            "version": "taskflow_v1"
        }

# Global instance
task_flow = TaskFlow()