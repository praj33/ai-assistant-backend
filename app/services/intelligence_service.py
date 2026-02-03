from typing import Dict, Any
from datetime import datetime
from app.external.intelligence.intelligence_service import IntelligenceCore

class IntelligenceService:
    def __init__(self):
        self.intelligence_core = IntelligenceCore()
        
    def process_interaction(self, context: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        output, bucket_write = self.intelligence_core.process_interaction(
            context=context,
            karma_data=context.get("karma_data"),
            bucket_data=context.get("bucket_data")
        )
        output["trace_id"] = trace_id
        return output
    
    def get_status(self) -> Dict[str, Any]:
        return {"service": "intelligence_service", "status": "active"}