"""
Execution Service Adapter - Chandresh Integration
Handles real WhatsApp, Email, and Instagram execution via Unified Action Orchestration
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Import real executors
from app.executors.whatsapp_executor import WhatsAppExecutor
from app.executors.email_executor import EmailExecutor
from app.executors.instagram_executor import InstagramExecutor

class ExecutionService:
    """Real execution service for WhatsApp, Email, and Instagram actions"""
    
    def __init__(self):
        self.whatsapp = WhatsAppExecutor()
        self.email = EmailExecutor()
        self.instagram = InstagramExecutor()
        
    def execute_action(self, action_type: str, action_data: Dict[str, Any], trace_id: str, enforcement_decision: str) -> Dict[str, Any]:
        """
        Execute action based on enforcement decision using real platform APIs
        
        Args:
            action_type: Type of action ('whatsapp', 'email', 'instagram')
            action_data: Action parameters
            trace_id: Trace ID for logging
            enforcement_decision: Enforcement decision (ALLOW, BLOCK, REWRITE)
            
        Returns:
            Dict with execution result
        """
        try:
            # Harden execution boundary - never trust caller blindly
            # Require explicit ALLOW decision for execution
            if enforcement_decision != "ALLOW":
                return {
                    "status": "blocked",
                    "action_type": action_type,
                    "reason": f"Action blocked by enforcement policy: {enforcement_decision}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": "execution_service"
                }
            
            # Apply rewrite if needed
            if enforcement_decision == "REWRITE":
                action_data = self._apply_rewrite(action_data, action_type)
            
            # Route to appropriate real execution method
            if action_type.lower() == "whatsapp":
                return self.whatsapp.send_message(
                    to_number=action_data.get("recipient", action_data.get("to", "")),
                    message=action_data.get("message", ""),
                    trace_id=trace_id
                )
            elif action_type.lower() == "email":
                return self.email.send_message(
                    to_email=action_data.get("recipient", action_data.get("to", "")),
                    subject=action_data.get("subject", "Message from AI Assistant"),
                    message=action_data.get("body", action_data.get("message", "")),
                    trace_id=trace_id
                )
            elif action_type.lower() == "instagram":
                return self.instagram.send_message(
                    recipient_id=action_data.get("recipient", action_data.get("to", "")),
                    message=action_data.get("message", ""),
                    trace_id=trace_id
                )
            else:
                return {
                    "status": "failed",
                    "action_type": action_type,
                    "error": f"Unsupported action type: {action_type}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": "execution_service"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "action_type": action_type,
                "error": str(e),
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "execution_service"
            }
    
    def _apply_rewrite(self, action_data: Dict[str, Any], action_type: str) -> Dict[str, Any]:
        """Apply enforcement rewrite to action data"""
        rewritten_data = action_data.copy()
        
        if action_type.lower() == "whatsapp":
            rewritten_data["message"] = "This message has been rewritten for safety compliance."
        elif action_type.lower() == "email":
            rewritten_data["body"] = "This email content has been rewritten for safety compliance."
            rewritten_data["subject"] = "[REWRITTEN] " + action_data.get("subject", "AI Assistant Message")
        elif action_type.lower() == "instagram":
            rewritten_data["message"] = "This message has been rewritten for safety compliance."
        
        return rewritten_data
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": "execution_service",
            "status": "active",
            "platforms": ["whatsapp", "email", "instagram"],
            "real_execution": True,
            "timestamp": datetime.utcnow().isoformat()
        }