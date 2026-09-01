-- Schema for the task review application.
-- Applied by app/db.py on startup; written to be safe to run repeatedly.

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL,

    -- The API validates these with Pydantic enums as well. Keeping the constraint
    -- in the database too means an invalid row cannot be written by any route in,
    -- including a manual sqlite3 session.
    priority    TEXT    NOT NULL CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH')),
    status      TEXT    NOT NULL CHECK (status   IN ('NEW', 'IN_PROGRESS', 'COMPLETED')),

    -- SQLite has no native date type; ISO 8601 UTC sorts correctly as text.
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- The task list is filtered by status, so that column is worth an index.
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status);
