"""
Calendar Executor — Chandresh Integration
Manages Google Calendar events via API.
Supports: create_event, update_event, delete_event, list_events.
Simulation mode when GOOGLE_CALENDAR_CREDENTIALS not configured.
"""

import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class CalendarExecutor:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_CALENDAR_API_KEY")
        self.access_token = os.getenv("GOOGLE_CALENDAR_ACCESS_TOKEN")
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
        self.base_url = "https://www.googleapis.com/calendar/v3"

    def _is_configured(self) -> bool:
        return bool(self.access_token or self.api_key)

    def create_event(self, title: str, start_time: str, end_time: str = None,
                     description: str = "", location: str = "", trace_id: str = "") -> Dict[str, Any]:
        """Create a calendar event."""
        try:
            # Default end_time = start_time + 1 hour
            if not end_time:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    end_dt = start_dt + timedelta(hours=1)
                    end_time = end_dt.isoformat()
                except Exception:
                    end_time = start_time

            event_data = {
                "summary": title,
                "description": description,
                "location": location,
                "start": {"dateTime": start_time, "timeZone": "Asia/Kolkata"},
                "end": {"dateTime": end_time, "timeZone": "Asia/Kolkata"},
            }

            if not self._is_configured():
                logger.info(f"[{trace_id}] Calendar simulation: creating event '{title}'")
                return {
                    "status": "success",
                    "event_id": f"sim_evt_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "action": "create_event",
                    "event": event_data,
                    "method": "calendar_simulation",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "calendar",
                    "note": "Simulation mode — set GOOGLE_CALENDAR_ACCESS_TOKEN for live execution"
                }

            url = f"{self.base_url}/calendars/{self.calendar_id}/events"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            logger.info(f"[{trace_id}] Creating calendar event: {title}")
            response = requests.post(url, json=event_data, headers=headers, timeout=30)

            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "status": "success",
                    "event_id": result.get("id"),
                    "action": "create_event",
                    "event": event_data,
                    "html_link": result.get("htmlLink"),
                    "method": "google_calendar_api",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "calendar"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Calendar API error: {response.status_code} - {response.text}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"[{trace_id}] Calendar create_event failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}

    def update_event(self, event_id: str, updates: Dict[str, Any], trace_id: str = "") -> Dict[str, Any]:
        """Update an existing calendar event."""
        try:
            if not self._is_configured():
                logger.info(f"[{trace_id}] Calendar simulation: updating event {event_id}")
                return {
                    "status": "success",
                    "event_id": event_id,
                    "action": "update_event",
                    "updates": updates,
                    "method": "calendar_simulation",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "calendar",
                    "note": "Simulation mode"
                }

            url = f"{self.base_url}/calendars/{self.calendar_id}/events/{event_id}"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            response = requests.patch(url, json=updates, headers=headers, timeout=30)
            if response.status_code == 200:
                return {
                    "status": "success", "event_id": event_id, "action": "update_event",
                    "updates": updates, "method": "google_calendar_api",
                    "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat(),
                    "platform": "calendar"
                }
            else:
                return {"status": "error", "error": f"Calendar API error: {response.status_code}",
                        "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}

        except Exception as e:
            logger.error(f"[{trace_id}] Calendar update_event failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}

    def delete_event(self, event_id: str, trace_id: str = "") -> Dict[str, Any]:
        """Delete a calendar event."""
        try:
            if not self._is_configured():
                logger.info(f"[{trace_id}] Calendar simulation: deleting event {event_id}")
                return {
                    "status": "success", "event_id": event_id, "action": "delete_event",
                    "method": "calendar_simulation", "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(), "platform": "calendar",
                    "note": "Simulation mode"
                }

            url = f"{self.base_url}/calendars/{self.calendar_id}/events/{event_id}"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.delete(url, headers=headers, timeout=30)

            if response.status_code == 204:
                return {
                    "status": "success", "event_id": event_id, "action": "delete_event",
                    "method": "google_calendar_api", "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(), "platform": "calendar"
                }
            else:
                return {"status": "error", "error": f"Calendar API error: {response.status_code}",
                        "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}

        except Exception as e:
            logger.error(f"[{trace_id}] Calendar delete_event failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}

    def list_events(self, max_results: int = 10, trace_id: str = "") -> Dict[str, Any]:
        """List upcoming calendar events."""
        try:
            if not self._is_configured():
                return {
                    "status": "success", "action": "list_events", "events": [],
                    "method": "calendar_simulation", "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(), "platform": "calendar",
                    "note": "Simulation mode"
                }

            url = f"{self.base_url}/calendars/{self.calendar_id}/events"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {
                "maxResults": max_results,
                "timeMin": datetime.utcnow().isoformat() + "Z",
                "orderBy": "startTime",
                "singleEvents": True
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                events = [{
                    "id": e.get("id"), "title": e.get("summary"),
                    "start": e.get("start", {}).get("dateTime"),
                    "end": e.get("end", {}).get("dateTime"),
                    "location": e.get("location", "")
                } for e in data.get("items", [])]
                return {
                    "status": "success", "action": "list_events", "events": events,
                    "method": "google_calendar_api", "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(), "platform": "calendar"
                }
            else:
                return {"status": "error", "error": f"Calendar API error: {response.status_code}",
                        "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}

        except Exception as e:
            logger.error(f"[{trace_id}] Calendar list_events failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}
