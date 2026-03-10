from __future__ import annotations

import datetime
import logging
import os
import time
from typing import Dict, List, Optional

from dotenv import load_dotenv
from pymongo import MongoClient

logger = logging.getLogger(__name__)

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class MongoDBClient:
    _shared_client = None
    _shared_db = None
    _connection_attempted = False
    _last_error: Optional[str] = None

    def __init__(self, max_retries: Optional[int] = None, retry_delay: Optional[float] = None):
        self.client = None
        self.db = None
        self.max_retries = max_retries if max_retries is not None else int(os.getenv("BUCKET_MONGO_MAX_RETRIES", "2"))
        self.retry_delay = retry_delay if retry_delay is not None else float(os.getenv("BUCKET_MONGO_RETRY_DELAY_SECONDS", "0.5"))
        self.server_selection_timeout_ms = int(os.getenv("BUCKET_MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))
        self.connect_timeout_ms = int(os.getenv("BUCKET_MONGO_CONNECT_TIMEOUT_MS", "5000"))
        self.socket_timeout_ms = int(os.getenv("BUCKET_MONGO_SOCKET_TIMEOUT_MS", "5000"))
        self.database_name = os.getenv("BUCKET_MONGO_DATABASE", "workflow_ai")
        self.connect()

    @classmethod
    def connection_error(cls) -> Optional[str]:
        return cls._last_error

    @classmethod
    def reset_cache(cls) -> None:
        if cls._shared_client is not None:
            try:
                cls._shared_client.close()
            except Exception:
                pass
        cls._shared_client = None
        cls._shared_db = None
        cls._connection_attempted = False
        cls._last_error = None

    def connect(self) -> None:
        cls = type(self)

        if cls._connection_attempted:
            self.client = cls._shared_client
            self.db = cls._shared_db
            return

        cls._connection_attempted = True

        if not _env_bool("BUCKET_MONGO_ENABLED", True):
            cls._last_error = "bucket_mongo_disabled"
            logger.warning("Bucket MongoDB disabled by BUCKET_MONGO_ENABLED; using in-memory fallback")
            return

        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            cls._last_error = "MONGODB_URI not configured"
            logger.warning("MONGODB_URI not configured; using in-memory fallback")
            return

        client_kwargs = {
            "serverSelectionTimeoutMS": self.server_selection_timeout_ms,
            "connectTimeoutMS": self.connect_timeout_ms,
            "socketTimeoutMS": self.socket_timeout_ms,
            "retryWrites": False,
        }

        for attempt in range(1, self.max_retries + 1):
            client = None
            try:
                logger.debug("Attempting MongoDB connection (attempt %s)", attempt)
                client = MongoClient(mongo_uri, **client_kwargs)
                db = client[self.database_name]
                client.admin.command("ping")

                self.client = client
                self.db = db
                cls._shared_client = client
                cls._shared_db = db
                cls._last_error = None
                logger.info("Successfully connected to MongoDB")
                return
            except Exception as exc:
                cls._last_error = str(exc)
                logger.warning("MongoDB connection attempt %s failed: %s", attempt, exc)
                if client is not None:
                    try:
                        client.close()
                    except Exception:
                        pass
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        logger.warning("MongoDB unavailable; continuing with in-memory fallback")

    def store_log(self, agent_name: str, message: str, details: Optional[Dict] = None):
        if self.db is None:
            logger.debug("No MongoDB connection available for store_log")
            return

        try:
            log_entry = {
                "agent": agent_name,
                "message": message,
                "timestamp": datetime.datetime.now(datetime.timezone.utc),
                "level": "info",
            }
            if details:
                log_entry.update(details)
            self.db.logs.insert_one(log_entry)
        except Exception as exc:
            logger.error("Failed to store log for %s: %s", agent_name, exc)

    def get_logs(self, agent_name: Optional[str] = None) -> List[Dict]:
        if self.db is None:
            logger.debug("No MongoDB connection available for get_logs")
            return []

        try:
            query = {"agent": agent_name} if agent_name else {}
            return list(self.db.logs.find(query))
        except Exception as exc:
            logger.error("Failed to retrieve logs: %s", exc)
            return []

    def close(self):
        if self.client:
            self.client.close()
            logger.debug("MongoDB connection closed")
