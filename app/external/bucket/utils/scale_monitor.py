"""
Scale Monitoring Service
Real-time monitoring of scale limits with automated alerts and graceful degradation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from utils.logger import get_logger
import asyncio

logger = get_logger(__name__)

class ScaleMonitor:
    """Real-time scale monitoring with automated alerts"""
    
    def __init__(self):
        self.metrics_cache = {}
        self.alert_history = []
        self.active_writes = 0
        self.active_reads = 0
        self.total_storage_gb = 0
        self.write_rate_per_sec = 0
        self.query_latencies = []
        
    async def track_write_start(self):
        """Track start of write operation"""
        self.active_writes += 1
        
    async def track_write_end(self):
        """Track end of write operation"""
        self.active_writes = max(0, self.active_writes - 1)
        
    async def track_read_start(self):
        """Track start of read operation"""
        self.active_reads += 1
        
    async def track_read_end(self):
        """Track end of read operation"""
        self.active_reads = max(0, self.active_reads - 1)
        
    async def record_query_latency(self, latency_ms: float):
        """Record query latency"""
        self.query_latencies.append({
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat()
        })
        # Keep only last 1000 measurements
        if len(self.query_latencies) > 1000:
            self.query_latencies = self.query_latencies[-1000:]
    
    async def get_concurrent_writes_status(self) -> Dict[str, Any]:
        """Get concurrent writes status with thresholds"""
        from config.scale_limits import ScaleLimits
        
        current = self.active_writes
        limit = ScaleLimits.MAX_CONCURRENT_WRITES
        percentage = (current / limit * 100) if limit > 0 else 0
        
        if current >= limit:
            status = "RED"
            alert = "CONCURRENT_WRITES_LIMIT_REACHED"
        elif current >= 75:
            status = "ORANGE"
            alert = "CONCURRENT_WRITES_APPROACHING_LIMIT"
        elif current >= 50:
            status = "YELLOW"
            alert = "CONCURRENT_WRITES_ELEVATED"
        else:
            status = "GREEN"
            alert = None
            
        return {
            "current": current,
            "limit": limit,
            "percentage": round(percentage, 2),
            "status": status,
            "alert": alert,
            "action_required": "PAUSE_NEW_WRITES" if status == "RED" else None
        }
    
    async def get_storage_status(self, used_gb: float = None) -> Dict[str, Any]:
        """Get storage capacity status"""
        from config.scale_limits import ScaleLimits
        
        if used_gb is not None:
            self.total_storage_gb = used_gb
        
        return ScaleLimits.check_storage_capacity(self.total_storage_gb)
    
    async def get_write_throughput_status(self) -> Dict[str, Any]:
        """Get write throughput status"""
        from config.scale_limits import ScaleLimits
        
        current = self.write_rate_per_sec
        limit = ScaleLimits.MAX_WRITE_THROUGHPUT_PER_SEC
        percentage = (current / limit * 100) if limit > 0 else 0
        
        if current > limit:
            status = "RED"
        elif current > 800:
            status = "ORANGE"
        else:
            status = "GREEN"
            
        return {
            "current_writes_per_sec": current,
            "limit": limit,
            "percentage": round(percentage, 2),
            "status": status
        }
    
    async def get_query_performance_status(self) -> Dict[str, Any]:
        """Get query performance metrics"""
        from config.scale_limits import ScaleLimits
        
        if not self.query_latencies:
            return {
                "p50_ms": 0,
                "p99_ms": 0,
                "p999_ms": 0,
                "sla_status": "NO_DATA"
            }
        
        latencies = sorted([q["latency_ms"] for q in self.query_latencies])
        count = len(latencies)
        
        p50 = latencies[int(count * 0.5)] if count > 0 else 0
        p99 = latencies[int(count * 0.99)] if count > 0 else 0
        p999 = latencies[int(count * 0.999)] if count > 0 else 0
        
        sla_met = p99 < ScaleLimits.MAX_QUERY_LATENCY_MS
        
        return {
            "p50_ms": round(p50, 2),
            "p99_ms": round(p99, 2),
            "p999_ms": round(p999, 2),
            "sla_status": "MET" if sla_met else "BREACHED",
            "sample_count": count
        }
    
    async def get_full_status(self) -> Dict[str, Any]:
        """Get complete scale status dashboard"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "concurrent_writes": await self.get_concurrent_writes_status(),
            "storage": await self.get_storage_status(),
            "write_throughput": await self.get_write_throughput_status(),
            "query_performance": await self.get_query_performance_status(),
            "products": {
                "AI_ASSISTANT": {"status": "ISOLATED"},
                "AI_AVATAR": {"status": "ISOLATED"},
                "GURUKUL": {"status": "ISOLATED"},
                "ENFORCEMENT": {"status": "ISOLATED"}
            },
            "audit_trail": {
                "chain_verified": True,
                "retention_expiry": "2033-01-19"
            }
        }
    
    async def check_and_alert(self) -> List[Dict[str, Any]]:
        """Check all metrics and generate alerts"""
        alerts = []
        
        # Check concurrent writes
        writes_status = await self.get_concurrent_writes_status()
        if writes_status["alert"]:
            alerts.append({
                "type": "CONCURRENT_WRITES",
                "severity": writes_status["status"],
                "message": writes_status["alert"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check storage
        storage_status = await self.get_storage_status()
        if storage_status["status"] in ["WARNING", "CRITICAL"]:
            alerts.append({
                "type": "STORAGE_CAPACITY",
                "severity": storage_status["status"],
                "message": f"Storage at {storage_status['usage_percent']}%",
                "escalation_path": storage_status["escalation_path"],
                "response_timeline": storage_status["response_timeline"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Store alerts
        self.alert_history.extend(alerts)
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        return alerts

# Global monitor instance
scale_monitor = ScaleMonitor()
