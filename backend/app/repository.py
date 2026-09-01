"""Data access for tasks: raw, parameterised SQL against SQLite.

Every value reaching SQLite is bound as a parameter rather than interpolated into
the statement. The statements themselves are written out in full as literals — no
f-strings, no fragments joined at runtime — so no input can influence the SQL text.
"""

import sqlite3

from app.models import Priority, Status, Task

# Newest first: an operations queue is read from the most recent item down.
_SELECT_ALL = """
    SELECT id, title, description, priority, status, created_at
    FROM tasks
    ORDER BY created_at DESC, id DESC
"""

_SELECT_BY_STATUS = """
    SELECT id, title, description, priority, status, created_at
    FROM tasks
    WHERE status = ?
    ORDER BY created_at DESC, id DESC
"""

_SELECT_ONE = """
    SELECT id, title, description, priority, status, created_at
    FROM tasks
    WHERE id = ?
"""

_UPDATE_STATUS = "UPDATE tasks SET status = ? WHERE id = ?"

# Written out separately rather than building "SET <column> = ?" at runtime:
# a column name assembled from a variable is the kind of string-built SQL the
# linter flags, and two literals are clearer than one clever statement.
_UPDATE_PRIORITY = "UPDATE tasks SET priority = ? WHERE id = ?"


def _to_task(row: sqlite3.Row) -> Task:
    return Task(**dict(row))


def list_tasks(conn: sqlite3.Connection, status: Status | None = None) -> list[Task]:
    """Return all tasks, optionally narrowed to a single status."""
    if status is None:
        rows = conn.execute(_SELECT_ALL).fetchall()
    else:
        rows = conn.execute(_SELECT_BY_STATUS, (status.value,)).fetchall()
    return [_to_task(row) for row in rows]


def get_task(conn: sqlite3.Connection, task_id: int) -> Task | None:
    """Return one task, or None when the id does not exist."""
    row = conn.execute(_SELECT_ONE, (task_id,)).fetchone()
    return _to_task(row) if row is not None else None


def update_status(conn: sqlite3.Connection, task_id: int, status: Status) -> Task | None:
    """Set a task's status and return the updated row, or None if it was not found."""
    cursor = conn.execute(_UPDATE_STATUS, (status.value, task_id))
    if cursor.rowcount == 0:
        return None
    return get_task(conn, task_id)


def update_priority(conn: sqlite3.Connection, task_id: int, priority: Priority) -> Task | None:
    """Set a task's priority and return the updated row, or None if not found."""
    cursor = conn.execute(_UPDATE_PRIORITY, (priority.value, task_id))
    if cursor.rowcount == 0:
        return None
    return get_task(conn, task_id)
