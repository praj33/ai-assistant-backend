from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from typing import List, Optional, Dict, Any

# FIXED IMPORT ✔
from ..core.database import get_db, Task
from ..core.taskflow import task_flow

router = APIRouter()


class TaskClassificationRequest(BaseModel):
    intent: str
    entities: Dict[str, Any] = {}
    context: Dict[str, Any] = {}
    original_text: str = ""
    confidence: float = 0.8
    text: str = ""  # Add text field for PDF rules


class TaskRequest(BaseModel):
    description: str


class TaskUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    description: str
    status: str
    created_at: str
    updated_at: str


@router.post("/task")
async def create_task_classification(request: TaskClassificationRequest):
    """Cognitive task mapping - convert intent data to structured task."""
    task = task_flow.build_task(request.dict())
    return {"task": task}


@router.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest, db: AsyncSession = Depends(get_db)):
    task = Task(description=request.description)
    db.add(task)
    await db.commit()
    await db.refresh(task)

    return TaskResponse(
        id=task.id,
        description=task.description,
        status=task.status,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat()
    )


@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task))
    tasks = result.scalars().all()

    return [
        TaskResponse(
            id=t.id,
            description=t.description,
            status=t.status,
            created_at=t.created_at.isoformat(),
            updated_at=t.updated_at.isoformat()
        )
        for t in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_by_id(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(
        id=task.id,
        description=task.description,
        status=task.status,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat()
    )


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, request: TaskUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = {}

    if request.description is not None:
        update_data["description"] = request.description

    if request.status is not None:
        update_data["status"] = request.status

    if update_data:
        await db.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(**update_data)
        )
        await db.commit()
        await db.refresh(task)

    return TaskResponse(
        id=task.id,
        description=task.description,
        status=task.status,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat()
    )


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.execute(delete(Task).where(Task.id == task_id))
    await db.commit()

    return {"message": "Task deleted successfully"}
