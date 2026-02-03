import redis
import json
import time
import uuid
from typing import Dict, List, Optional, Any
from utils.logger import logger
import os
from datetime import datetime, timedelta

class RedisService:
    """Enhanced Redis service for agent and basket execution management"""
    
    def __init__(self):
        self.client = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """Initialize Redis connection with retry logic"""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            redis_password = os.getenv("REDIS_PASSWORD", None)
            
            self.client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.client.ping()
            self.connected = True
            logger.info(f"Redis connected successfully at {redis_host}:{redis_port}")
            
        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Redis connection failed: {e}")
            self.connected = False
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected and responsive"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except (redis.ConnectionError, redis.RedisError):
            self.connected = False
            return False
    
    def store_execution_log(self, execution_id: str, agent_name: str, step: str, data: Dict, status: str = "success"):
        """Store detailed execution logs for agents and baskets"""
        if not self.is_connected():
            logger.warning("Redis not connected, skipping log storage")
            return
        
        try:
            log_entry = {
                "execution_id": execution_id,
                "agent_name": agent_name,
                "step": step,
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "data": data
            }
            
            # Store in execution-specific list
            key = f"execution:{execution_id}:logs"
            self.client.lpush(key, json.dumps(log_entry))
            self.client.expire(key, 86400)  # Expire after 24 hours
            
            # Store in agent-specific list
            agent_key = f"agent:{agent_name}:logs"
            self.client.lpush(agent_key, json.dumps(log_entry))
            self.client.ltrim(agent_key, 0, 999)  # Keep last 1000 logs
            
            logger.debug(f"Stored execution log: {execution_id} - {agent_name} - {step}")
            
        except Exception as e:
            logger.error(f"Failed to store execution log: {e}")
    
    def store_agent_state(self, agent_name: str, execution_id: str, state: Dict):
        """Store agent state during execution"""
        if not self.is_connected():
            return
        
        try:
            key = f"agent:{agent_name}:state:{execution_id}"
            self.client.hset(key, mapping={
                "state": json.dumps(state),
                "timestamp": datetime.now().isoformat(),
                "execution_id": execution_id
            })
            self.client.expire(key, 3600)  # Expire after 1 hour
            
        except Exception as e:
            logger.error(f"Failed to store agent state: {e}")
    
    def get_agent_state(self, agent_name: str, execution_id: str) -> Optional[Dict]:
        """Retrieve agent state"""
        if not self.is_connected():
            return None
        
        try:
            key = f"agent:{agent_name}:state:{execution_id}"
            state_data = self.client.hget(key, "state")
            if state_data:
                return json.loads(state_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get agent state: {e}")
            return None
    
    def store_basket_execution(self, basket_name: str, execution_id: str, config: Dict, status: str = "started"):
        """Store basket execution metadata"""
        if not self.is_connected():
            return
        
        try:
            key = f"basket:{basket_name}:execution:{execution_id}"
            execution_data = {
                "basket_name": basket_name,
                "execution_id": execution_id,
                "config": json.dumps(config),
                "status": status,
                "started_at": datetime.now().isoformat(),
                "agents": json.dumps(config.get("agents", [])),
                "strategy": config.get("execution_strategy", "sequential")
            }
            
            self.client.hset(key, mapping=execution_data)
            self.client.expire(key, 86400)  # Expire after 24 hours
            
            # Add to basket execution list
            list_key = f"basket:{basket_name}:executions"
            self.client.lpush(list_key, execution_id)
            self.client.ltrim(list_key, 0, 99)  # Keep last 100 executions
            
        except Exception as e:
            logger.error(f"Failed to store basket execution: {e}")
    
    def update_basket_status(self, basket_name: str, execution_id: str, status: str, result: Optional[Dict] = None):
        """Update basket execution status"""
        if not self.is_connected():
            return
        
        try:
            key = f"basket:{basket_name}:execution:{execution_id}"
            update_data = {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            
            if result:
                update_data["result"] = json.dumps(result)
            
            if status in ["completed", "failed"]:
                update_data["completed_at"] = datetime.now().isoformat()
            
            self.client.hset(key, mapping=update_data)
            
        except Exception as e:
            logger.error(f"Failed to update basket status: {e}")
    
    def get_execution_logs(self, execution_id: str, limit: int = 100) -> List[Dict]:
        """Get execution logs for a specific execution"""
        if not self.is_connected():
            return []
        
        try:
            key = f"execution:{execution_id}:logs"
            logs = self.client.lrange(key, 0, limit - 1)
            return [json.loads(log) for log in logs]
            
        except Exception as e:
            logger.error(f"Failed to get execution logs: {e}")
            return []
    
    def get_agent_logs(self, agent_name: str, limit: int = 100) -> List[Dict]:
        """Get logs for a specific agent"""
        if not self.is_connected():
            return []
        
        try:
            key = f"agent:{agent_name}:logs"
            logs = self.client.lrange(key, 0, limit - 1)
            return [json.loads(log) for log in logs]
            
        except Exception as e:
            logger.error(f"Failed to get agent logs: {e}")
            return []
    
    def store_agent_output(self, execution_id: str, agent_name: str, output: Dict):
        """Store agent output for passing between agents"""
        if not self.is_connected():
            return
        
        try:
            key = f"execution:{execution_id}:outputs:{agent_name}"
            self.client.set(key, json.dumps(output), ex=3600)  # Expire after 1 hour
            
        except Exception as e:
            logger.error(f"Failed to store agent output: {e}")
    
    def get_agent_output(self, execution_id: str, agent_name: str) -> Optional[Dict]:
        """Get agent output for use by subsequent agents"""
        if not self.is_connected():
            return None
        
        try:
            key = f"execution:{execution_id}:outputs:{agent_name}"
            output_data = self.client.get(key)
            if output_data:
                return json.loads(output_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get agent output: {e}")
            return None
    
    def generate_execution_id(self) -> str:
        """Generate unique execution ID"""
        return f"{int(time.time())}_{uuid.uuid4().hex[:8]}"

    def get_basket_executions(self, basket_name: str) -> list:
        """Get all execution IDs for a specific basket"""
        if not self.connected:
            return []

        try:
            # Get execution IDs from the basket executions list
            executions = self.client.lrange(f"basket:{basket_name}:executions", 0, -1)
            return [exec_id.decode() if isinstance(exec_id, bytes) else exec_id for exec_id in executions]
        except Exception as e:
            logger.error(f"Error getting basket executions: {e}")
            return []

    def cleanup_old_data(self, days: int = 7):
        """Clean up old execution data"""
        if not self.is_connected():
            return
        
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_timestamp = cutoff_time.timestamp()
            
            # This is a basic cleanup - in production, you'd want more sophisticated cleanup
            pattern = "execution:*"
            for key in self.client.scan_iter(match=pattern):
                try:
                    # Check if key is old enough to delete
                    key_parts = key.split(":")
                    if len(key_parts) >= 2:
                        timestamp_part = key_parts[1].split("_")[0]
                        if timestamp_part.isdigit() and int(timestamp_part) < cutoff_timestamp:
                            self.client.delete(key)
                except:
                    continue
                    
            logger.info(f"Cleaned up Redis data older than {days} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def get_stats(self) -> Dict:
        """Get Redis usage statistics"""
        if not self.is_connected():
            return {"connected": False}
        
        try:
            info = self.client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace": info.get("db0", {})
            }
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {"connected": False, "error": str(e)}
    
    def close(self):
        """Close Redis connection"""
        if self.client:
            try:
                self.client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self.client = None
                self.connected = False
