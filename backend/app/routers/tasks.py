"""Task endpoints: GET /tasks and PATCH /tasks/{task_id}/status."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.db import get_connection
from app.models import Status, StatusUpdate, Task
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Annotated dependencies keep the callables out of argument defaults, which is the
# current FastAPI style and avoids the mutable-default trap flake8-bugbear warns about.
DbConnection = Annotated[sqlite3.Connection, Depends(get_connection)]


@router.get("", response_model=list[Task])
def list_tasks(
    conn: DbConnection,
    status: Annotated[
        Status | None,
        Query(description="Optional status filter. Omit to return every task."),
    ] = None,
) -> list[Task]:
    """List tasks, newest first, optionally filtered by status."""
    return task_service.list_tasks(conn, status)


@router.patch("/{task_id}/status", response_model=Task)
def update_task_status(
    task_id: int,
    payload: StatusUpdate,
    conn: DbConnection,
) -> Task:
    """Update a task's status.

    `payload.status` is typed as the Status enum, so an unsupported value is
    rejected by validation before this function runs. A missing task id raises
    TaskNotFoundError, which the app translates into a 404.
    """
    return task_service.update_task_status(conn, task_id, payload.status)
