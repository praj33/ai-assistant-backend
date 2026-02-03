import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Add AI-Being path for imports
ai_being_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'AI-Being')
if ai_being_path not in sys.path:
    sys.path.append(ai_being_path)

from behavior_validator import validate_behavior

class SafetyService:
    def __init__(self):
        pass
        
    def validate_content(self, content: str, trace_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        result = validate_behavior(
            intent="auto",
            conversational_output=content,
            age_gate_status=context.get("age_gate_status", False) if context else False,
            region_rule_status=context.get("region_rule_status") if context else None,
            platform_policy_state=context.get("platform_policy_state") if context else None,
            karma_bias_input=context.get("karma_bias_input", 0.5) if context else 0.5
        )
        
        result["trace_id"] = trace_id
        result["timestamp"] = datetime.utcnow().isoformat()
        return result
    
    def get_status(self) -> Dict[str, Any]:
        return {"service": "safety_service", "status": "active"}