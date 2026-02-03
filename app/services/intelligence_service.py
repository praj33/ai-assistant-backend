import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Add unified-ai-being intelligence service path
unified_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'unified-ai-being', 'backend', 'app', 'services')
if unified_path not in sys.path:
    sys.path.append(unified_path)

from intelligence_service import IntelligenceCore

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