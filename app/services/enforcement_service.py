import sys
import os
from typing import Dict, Any
from datetime import datetime

# Add unified-ai-being enforcement service path
unified_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'unified-ai-being', 'backend', 'app', 'services')
if unified_path not in sys.path:
    sys.path.append(unified_path)

from enforcement_service import EnforcementEngine

class EnforcementService:
    def __init__(self):
        self.enforcement_engine = EnforcementEngine()
        
    def enforce_policy(self, payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        verdict = self.enforcement_engine.enforce(payload)
        result = verdict.to_dict()
        result["trace_id"] = trace_id
        return result
    
    def get_status(self) -> Dict[str, Any]:
        return {"service": "enforcement_service", "status": "active"}