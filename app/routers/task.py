from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.core.database import tasks_collection

router = APIRouter()


class TaskClassificationRequest(BaseModel):
    intent: str
    entities: Dict[str, Any] = {}
    context: Dict[str, Any] = {}
    original_text: str = ""
    confidence: float = 0.8
    text: str = ""


class TaskRequest(BaseModel):
    description: str


class TaskUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None


class TaskResponse(BaseModel):
    trace_id: str
    task_type: str
    status: str
    execution: Dict[str, Any] = {}
    created_at: str
    updated_at: str


@router.get("/tasks")
async def get_all_tasks():
    """Get all tasks"""
    tasks = await tasks_collection.find().to_list(1000)
    for task in tasks:
        task["_id"] = str(task["_id"])
    return {"tasks": tasks}


@router.get("/tasks/{trace_id}")
async def get_task_by_trace_id(trace_id: str):
    """Get task by trace_id"""
    task = await tasks_collection.find_one({"trace_id": trace_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["_id"] = str(task["_id"])
    return task


@router.delete("/tasks/{trace_id}")
async def delete_task_by_trace_id(trace_id: str):
    """Delete task by trace_id"""
    result = await tasks_collection.delete_one({"trace_id": trace_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully", "trace_id": trace_id}
