from typing import Dict, Any
from datetime import datetime
from app.external.enforcement.enforcement_engine import EnforcementEngine

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