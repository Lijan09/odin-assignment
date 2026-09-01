"""Task use cases, sitting between the routers and the repository.

The service raises domain errors rather than HTTP errors. Translating those into
responses is the web layer's job, which keeps this module testable on its own.
"""

import sqlite3

from app import repository
from app.models import Status, Task


class TaskNotFoundError(Exception):
    """Raised when an operation targets a task id that does not exist."""

    def __init__(self, task_id: int) -> None:
        self.task_id = task_id
        super().__init__(f"Task {task_id} was not found.")


def list_tasks(conn: sqlite3.Connection, status: Status | None = None) -> list[Task]:
    return repository.list_tasks(conn, status)


def get_task(conn: sqlite3.Connection, task_id: int) -> Task:
    task = repository.get_task(conn, task_id)
    if task is None:
        raise TaskNotFoundError(task_id)
    return task


def update_task_status(conn: sqlite3.Connection, task_id: int, status: Status) -> Task:
    task = repository.update_status(conn, task_id, status)
    if task is None:
        raise TaskNotFoundError(task_id)
    return task
