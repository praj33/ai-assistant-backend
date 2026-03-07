"""
EMS Executor — Chandresh Integration (BHIV EMS)
Creates and manages EMS (Employee Management System) tasks.
Supports: create_task, assign_task, update_task.
Gateway-ready: connects to BHIV EMS API when available.
"""

import os
import requests
from typing import Dict, Any
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class EMSExecutor:
    def __init__(self):
        self.ems_api_url = os.getenv("EMS_API_URL")
        self.ems_api_key = os.getenv("EMS_API_KEY")

    def _is_configured(self) -> bool:
        return bool(self.ems_api_url and self.ems_api_key)

    def create_task(self, title: str, description: str = "", priority: str = "medium",
                    assignee: str = "", trace_id: str = "") -> Dict[str, Any]:
        """Create an EMS task."""
        try:
            task_id = f"ems_task_{uuid.uuid4().hex[:12]}"
            task_data = {
                "task_id": task_id,
                "title": title,
                "description": description,
                "priority": priority,
                "assignee": assignee,
                "status": "created",
                "created_at": datetime.utcnow().isoformat()
            }

            if not self._is_configured():
                logger.info(f"[{trace_id}] EMS simulation: creating task '{title}'")
                return {
                    "status": "success",
                    "action": "create_task",
                    **task_data,
                    "method": "ems_simulation",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "ems",
                    "note": "Simulation mode — set EMS_API_URL for live execution"
                }

            headers = {"Authorization": f"Bearer {self.ems_api_key}", "Content-Type": "application/json"}
            response = requests.post(f"{self.ems_api_url}/tasks", json=task_data, headers=headers, timeout=30)
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "status": "success", "action": "create_task", **task_data,
                    "method": "ems_api", "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(), "platform": "ems"
                }
            else:
                return {"status": "error", "error": f"EMS API error: {response.status_code}",
                        "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}

        except Exception as e:
            logger.error(f"[{trace_id}] EMS create_task failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}

    def assign_task(self, task_id: str, assignee: str, trace_id: str = "") -> Dict[str, Any]:
        """Assign an EMS task to a user."""
        try:
            if not self._is_configured():
                logger.info(f"[{trace_id}] EMS simulation: assigning {task_id} to {assignee}")
                return {
                    "status": "success", "action": "assign_task",
                    "task_id": task_id, "assignee": assignee,
                    "method": "ems_simulation", "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(), "platform": "ems",
                    "note": "Simulation mode"
                }

            headers = {"Authorization": f"Bearer {self.ems_api_key}", "Content-Type": "application/json"}
            response = requests.patch(
                f"{self.ems_api_url}/tasks/{task_id}",
                json={"assignee": assignee}, headers=headers, timeout=30
            )
            if response.status_code == 200:
                return {
                    "status": "success", "action": "assign_task",
                    "task_id": task_id, "assignee": assignee,
                    "method": "ems_api", "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(), "platform": "ems"
                }
            else:
                return {"status": "error", "error": f"EMS API error: {response.status_code}",
                        "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}

        except Exception as e:
            logger.error(f"[{trace_id}] EMS assign_task failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}

    def update_task(self, task_id: str, updates: Dict[str, Any], trace_id: str = "") -> Dict[str, Any]:
        """Update an EMS task."""
        try:
            if not self._is_configured():
                logger.info(f"[{trace_id}] EMS simulation: updating task {task_id}")
                return {
                    "status": "success", "action": "update_task",
                    "task_id": task_id, "updates": updates,
                    "method": "ems_simulation", "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(), "platform": "ems",
                    "note": "Simulation mode"
                }

            headers = {"Authorization": f"Bearer {self.ems_api_key}", "Content-Type": "application/json"}
            response = requests.patch(
                f"{self.ems_api_url}/tasks/{task_id}",
                json=updates, headers=headers, timeout=30
            )
            if response.status_code == 200:
                return {
                    "status": "success", "action": "update_task",
                    "task_id": task_id, "updates": updates,
                    "method": "ems_api", "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(), "platform": "ems"
                }
            else:
                return {"status": "error", "error": f"EMS API error: {response.status_code}",
                        "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}

        except Exception as e:
            logger.error(f"[{trace_id}] EMS update_task failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}
