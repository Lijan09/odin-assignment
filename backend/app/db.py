"""SQLite connection handling, schema initialisation and seed data.

Run directly to prepare a local database:

    python -m app.db            # create the schema and seed it if empty
    python -m app.db --reset    # drop everything and reseed
"""

import sqlite3
import sys
from collections.abc import Iterator
from pathlib import Path

from app.config import settings

# Paths are resolved against the backend directory rather than the working
# directory, so the app behaves the same however it is launched.
BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE_DIR / "schema.sql"

IN_MEMORY = ":memory:"

# Seeded tasks are drawn from Odin's actual operations work: Australian mortgage
# broking, tax and conveyancing for expats and overseas investors. Realistic rows
# make the AI analysis meaningful to look at, which "Task 1, Task 2" would not.
SEED_TASKS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "Missing customer document",
        "The customer submitted their application but has not provided their latest payslip.",
        "HIGH",
        "NEW",
        "2026-08-24T09:15:00Z",
    ),
    (
        "ID verification outstanding",
        "The second applicant's passport copy has not been certified. The lender "
        "will not progress the file until certified ID is on record.",
        "HIGH",
        "NEW",
        "2026-08-25T11:40:00Z",
    ),
    (
        "Settlement date moved",
        "The vendor has asked to bring settlement forward by one week. The "
        "conveyancer and the lender both need to confirm they can meet the new date.",
        "HIGH",
        "IN_PROGRESS",
        "2026-08-26T14:05:00Z",
    ),
    (
        "Valuation ordered",
        "A property valuation has been ordered with the lender for the Brisbane "
        "investment property. Awaiting the valuer's report.",
        "MEDIUM",
        "IN_PROGRESS",
        "2026-08-27T08:30:00Z",
    ),
    (
        "Tax residency query",
        "The client has asked whether they remain an Australian tax resident while "
        "working in Singapore, and how that affects their interest deductions.",
        "MEDIUM",
        "NEW",
        "2026-08-28T16:20:00Z",
    ),
    (
        "Lender follow-up",
        "No response from the lender on the conditional approval submitted nine "
        "days ago. Chase the BDM for an update.",
        "LOW",
        "COMPLETED",
        "2026-08-21T10:00:00Z",
    ),
)


def _database_target() -> str:
    """Resolve the configured database path, leaving ':memory:' untouched."""
    if settings.database_path == IN_MEMORY:
        return IN_MEMORY
    path = Path(settings.database_path)
    return str(path if path.is_absolute() else BASE_DIR / path)


def connect() -> sqlite3.Connection:
    """Open a connection with row access by column name and foreign keys enabled.

    check_same_thread=False is required, not optional. FastAPI runs a sync
    generator dependency and the endpoint that consumes it as separate
    run_in_threadpool calls, and AnyIO does not promise the same worker thread for
    both. Without this flag a connection opened during dependency setup raises
    ProgrammingError as soon as the endpoint runs on a different worker, which
    shows up as intermittent 500s under concurrent load.

    Disabling the check is safe here because the connection is not shared: each
    request gets its own, and setup, handler and teardown touch it strictly in
    sequence, never at the same time.
    """
    conn = sqlite3.connect(_database_target(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # SQLite disables foreign key enforcement by default, per connection.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_connection() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency yielding one connection per request.

    A connection per request keeps things safe under FastAPI's threadpool, which
    runs sync endpoints on different threads.
    """
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    """Apply schema.sql. The script is idempotent."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def count_tasks(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0])


def seed_tasks(conn: sqlite3.Connection, *, force: bool = False) -> int:
    """Insert the seed tasks, skipping if data already exists.

    Returns the number of rows inserted, so callers can report what happened.
    """
    if force:
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'tasks'")
    elif count_tasks(conn) > 0:
        return 0

    conn.executemany(
        """
        INSERT INTO tasks (title, description, priority, status, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        SEED_TASKS,
    )
    return len(SEED_TASKS)


def bootstrap(*, force: bool = False) -> int:
    """Create the schema and seed it. Used at startup and by the CLI below."""
    conn = connect()
    try:
        init_db(conn)
        inserted = seed_tasks(conn, force=force)
        conn.commit()
        return inserted
    finally:
        conn.close()


if __name__ == "__main__":
    reset = "--reset" in sys.argv[1:]
    inserted = bootstrap(force=reset)
    target = _database_target()
    if inserted:
        print(f"Seeded {inserted} tasks into {target}")
    else:
        print(f"Database at {target} already contains tasks; nothing to do")
