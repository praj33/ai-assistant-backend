from __future__ import annotations

"""
Mitra System Registry
Centralized registry for all core runtime modules.

Goal:
- Provide a single, deterministic place where system services are constructed.
- Prevent "hidden" instantiations of Safety / Intelligence / Enforcement / Execution / Bucket / Audio.
- Enable health reporting and BHIV/Core integrations to reason about the live system.
"""

from typing import Dict, Any

from app.services.safety_service import SafetyService
from app.services.intelligence_service import IntelligenceService
from app.services.enforcement_service import EnforcementService
from app.services.execution_service import ExecutionService
from app.services.bucket_service import BucketService
from app.services.audio_service import AudioService


class MitraSystemRegistry:
    def __init__(self) -> None:
        # Single shared instances for the whole runtime.
        self.safety_service = SafetyService()
        self.intelligence_service = IntelligenceService()
        self.enforcement_service = EnforcementService()
        self.execution_service = ExecutionService()
        self.bucket_service = BucketService()
        self.audio_service = AudioService()

    def snapshot(self) -> Dict[str, Any]:
        """
        Lightweight status snapshot of all registered modules.
        Used by health monitors and BHIV Core gateway.
        """
        return {
            "safety": self.safety_service.get_status(),
            "intelligence": self.intelligence_service.get_status(),
            "enforcement": self.enforcement_service.get_status(),
            "execution": self.execution_service.get_status(),
            "bucket": self.bucket_service.get_status()
            if hasattr(self.bucket_service, "get_status")
            else {"service": "bucket_service", "status": "unknown"},
            "audio": self.audio_service.get_tts_status()
            if hasattr(self.audio_service, "get_tts_status")
            else {"service": "audio_service", "status": "active"},
        }


# Global registry instance used across the runtime.
mitra_registry = MitraSystemRegistry()

