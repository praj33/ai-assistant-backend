"""
Telegram Contact Service

Stores and resolves mappings between Telegram usernames and chat IDs.
Uses MongoDB when available; falls back to an in-memory store otherwise.
This lets the assistant accept '@username' from the frontend while
always sending via numeric chat_id under the hood.
"""

from __future__ import annotations

from typing import Optional

from app.external.bucket.database.mongo_db import MongoDBClient


class TelegramContactService:
    _memory_store: dict[str, int] = {}

    def __init__(self) -> None:
        # Reuse existing Mongo client; if it fails, we stay in memory mode.
        try:
            self.mongo_client = MongoDBClient()
        except Exception:
            self.mongo_client = None

    @property
    def collection(self):
        if self.mongo_client and self.mongo_client.db is not None:
            return self.mongo_client.db.get_collection("telegram_contacts")
        return None

    def save_contact(self, username: Optional[str], chat_id: int) -> None:
        if not username:
            return
        username = username.lower()

        # In-memory always
        TelegramContactService._memory_store[username] = chat_id

        # Best-effort Mongo persistence
        coll = self.collection
        if coll:
            try:
                coll.update_one(
                    {"username": username},
                    {"$set": {"chat_id": chat_id}},
                    upsert=True,
                )
            except Exception:
                # Logging handled at MongoDBClient level; fail-soft here.
                pass

    def resolve_chat_id(self, username: str) -> Optional[int]:
        if not username:
            return None
        username = username.lower().lstrip("@")

        # Check in-memory
        if username in TelegramContactService._memory_store:
            return TelegramContactService._memory_store[username]

        # Check Mongo if available
        coll = self.collection
        if coll:
            try:
                doc = coll.find_one({"username": username})
                if doc and "chat_id" in doc:
                    chat_id = int(doc["chat_id"])
                    TelegramContactService._memory_store[username] = chat_id
                    return chat_id
            except Exception:
                return None

        return None

