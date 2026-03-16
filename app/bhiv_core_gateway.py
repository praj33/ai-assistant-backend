from __future__ import annotations

"""
BHIV Core Gateway

Thin integration layer that exposes the Mitra runtime to BHIV Core:
- Identity registration
- System health reporting
- Governance hooks

This module does NOT implement BHIV logic itself; it adapts Mitra's
internal services and health signals into a stable interface that
BHIV Core can call.
"""

from typing import Any, Dict
from datetime import datetime

from app.mitra_system_registry import mitra_registry
from app.core.bhiv_core import BHIVCore
from app.memory.memory_manager import MemoryManager
from app.agents.base_agent import BaseAgent
from app.tools.calculator_tool import CalculatorTool
from app.core.bhiv_reasoner import BHIVReasoner


def build_bhiv_core() -> BHIVCore:
    """
    Construct a BHIVCore instance wired to Mitra's memory, agents, and tools.
    This is a thin adapter; BHIVCore's internals live in app.core.bhiv_core.
    """
    memory_manager = MemoryManager()
    agents = [BaseAgent(name="mitra_core_agent")]
    tools = [CalculatorTool()]
    reasoner = BHIVReasoner()
    return BHIVCore(memory_manager, agents, tools, reasoner)


def register_identity() -> Dict[str, Any]:
    """
    Identity registration payload that BHIV Core can consume.
    """
    return {
        "system": "mitra_runtime",
        "version": "3.0.0",
        "modules": list(mitra_registry.snapshot().keys()),
        "registered_at": datetime.utcnow().isoformat(),
    }


def report_system_health() -> Dict[str, Any]:
    """
    Aggregate system health view for BHIV Core.
    """
    snapshot = mitra_registry.snapshot()
    return {
        "system": "mitra_runtime",
        "timestamp": datetime.utcnow().isoformat(),
        "modules": snapshot,
    }


def governance_hooks() -> Dict[str, Any]:
    """
    Governance hooks surface — BHIV Core can use this to enforce policies
    or to introspect Mitra's configuration. Currently a stub, but kept
    deterministic and structured for future expansion.
    """
    return {
        "system": "mitra_runtime",
        "hooks": {
            "enforcement_authority": "app.services.enforcement_service.EnforcementService",
            "execution_gateway": "app.services.execution_service.ExecutionService",
            "bucket_logging": "app.services.bucket_service.BucketService",
        },
    }

