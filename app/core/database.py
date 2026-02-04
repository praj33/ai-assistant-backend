import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ai_assistant")

client = AsyncIOMotorClient(MONGODB_URI)
db = client[DATABASE_NAME]

# Collections
tasks_collection = db["tasks"]
audit_collection = db["audit_logs"]

async def get_db():
    return db

async def create_tables():
    # MongoDB creates collections automatically
    # Create indexes for performance
    await tasks_collection.create_index("created_at")
    await tasks_collection.create_index("trace_id", unique=True)  # Add trace_id index
    await audit_collection.create_index("trace_id")
    await audit_collection.create_index("timestamp")