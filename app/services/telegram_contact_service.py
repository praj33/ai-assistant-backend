"""
Telegram Contact Service

Stores and resolves mappings between Telegram usernames and chat IDs.
Uses MongoDB when available; falls back to an in-memory store otherwise.
This lets the assistant accept '@username' from the frontend while
always sending via numeric chat_id under the hood.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List

from app.external.bucket.database.mongo_db import MongoDBClient


class TelegramContactService:
    # username -> chat_id
    _memory_store: dict[str, int] = {}
    # chat_id -> contact dict
    _contacts_by_chat_id: dict[int, Dict[str, Any]] = {}

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

    def save_contact(
        self,
        *,
        chat_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> None:
        """Store contact details in memory and Mongo (if available)."""
        display_name_parts = [p for p in [first_name, last_name] if p]
        display_name = " ".join(display_name_parts) if display_name_parts else username or str(chat_id)

        # In-memory: by chat_id
        contact = {
            "chat_id": int(chat_id),
            "username": (username or "").lower() or None,
            "first_name": first_name,
            "last_name": last_name,
            "display_name": display_name,
        }
        TelegramContactService._contacts_by_chat_id[int(chat_id)] = contact

        # In-memory: username -> chat_id mapping for resolution, when username exists
        if username:
            uname = username.lower()
            TelegramContactService._memory_store[uname] = int(chat_id)

        # Best-effort Mongo persistence
        coll = self.collection
        if coll:
            try:
                coll.update_one(
                    {"chat_id": int(chat_id)},
                    {
                        "$set": {
                            "chat_id": int(chat_id),
                            "username": (username or "").lower() or None,
                            "first_name": first_name,
                            "last_name": last_name,
                            "display_name": display_name,
                        }
                    },
                    upsert=True,
                )
            except Exception:
                # Logging handled at MongoDBClient level; fail-soft here.
                pass

    def save_from_telegram_message(self, chat: Dict[str, Any], sender: Dict[str, Any]) -> None:
        """Convenience helper to persist contact details from a Telegram update."""
        chat_id = chat.get("id")
        if chat_id is None:
            return
        username = sender.get("username")
        first_name = sender.get("first_name")
        last_name = sender.get("last_name")
        self.save_contact(chat_id=int(chat_id), username=username, first_name=first_name, last_name=last_name)

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
                    TelegramContactService._contacts_by_chat_id[chat_id] = {
                        "chat_id": chat_id,
                        "username": doc.get("username"),
                        "first_name": doc.get("first_name"),
                        "last_name": doc.get("last_name"),
                        "display_name": doc.get("display_name") or doc.get("username") or str(chat_id),
                    }
                    return chat_id
            except Exception:
                return None

        return None

    def list_contacts(self) -> List[Dict[str, Any]]:
        """Return a list of known contacts for UI selection."""
        coll = self.collection
        contacts: List[Dict[str, Any]] = []

        if coll:
            try:
                for doc in coll.find({}, {"_id": 0}):
                    contacts.append(
                        {
                            "chat_id": int(doc.get("chat_id")),
                            "username": doc.get("username"),
                            "first_name": doc.get("first_name"),
                            "last_name": doc.get("last_name"),
                            "display_name": doc.get("display_name")
                            or doc.get("username")
                            or str(doc.get("chat_id")),
                        }
                    )
            except Exception:
                pass

        if not contacts:
            # Fallback to in-memory store
            for chat_id, contact in TelegramContactService._contacts_by_chat_id.items():
                contacts.append(contact)

        # Sort for stable UI: by display_name then chat_id
        contacts.sort(key=lambda c: (c.get("display_name") or "", c.get("chat_id")))
        return contacts

