"""Task endpoints: GET /tasks and PATCH /tasks/{task_id}/status."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.ai.base import AiAnalyser
from app.ai.provider import get_analyser
from app.db import get_connection
from app.models import AnalysisResult, PriorityUpdate, Status, StatusUpdate, Task
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Annotated dependencies keep the callables out of argument defaults, which is the
# current FastAPI style and avoids the mutable-default trap flake8-bugbear warns about.
DbConnection = Annotated[sqlite3.Connection, Depends(get_connection)]
Analyser = Annotated[AiAnalyser, Depends(get_analyser)]


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


@router.patch("/{task_id}/priority", response_model=Task)
def update_task_priority(
    task_id: int,
    payload: PriorityUpdate,
    conn: DbConnection,
) -> Task:
    """Update a task's priority.

    Mirrors the status endpoint: the enum rejects unsupported values before this
    function runs, and an unknown id raises TaskNotFoundError for a 404.
    """
    return task_service.update_task_priority(conn, task_id, payload.priority)


@router.post("/{task_id}/analyse", response_model=AnalysisResult)
def analyse_task(task_id: int, conn: DbConnection, analyser: Analyser) -> AnalysisResult:
    """Analyse a task with AI and return the structured result.

    Spelled `analyse` to match the brief. The analyser is injected, so a test can
    substitute a failing implementation and exercise the error path without a
    network call. A provider failure raises AiAnalysisError, which the app turns
    into a 502.
    """
    return task_service.analyse_task(conn, task_id, analyser)
