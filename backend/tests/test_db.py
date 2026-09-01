"""Connection-level tests for the SQLite layer."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from app import db


@pytest.fixture
def in_memory_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point connect() at an in-memory database, never the developer's file."""
    monkeypatch.setattr(db.settings, "database_path", db.IN_MEMORY)


def test_connection_is_usable_from_another_thread(in_memory_settings: None) -> None:
    """Regression test for an intermittent 500 under concurrent load.

    FastAPI runs a sync generator dependency and the endpoint consuming it as two
    separate run_in_threadpool calls, and AnyIO does not guarantee the same worker
    thread for both. A connection pinned to its creating thread therefore raises
    sqlite3.ProgrammingError once the two land on different workers.
    """
    conn = db.connect()
    try:
        db.init_db(conn)
        db.seed_tasks(conn)
        conn.commit()

        # Use the connection from a thread other than the one that opened it.
        with ThreadPoolExecutor(max_workers=1) as pool:
            count = pool.submit(lambda: db.count_tasks(conn)).result()

        assert count == len(db.SEED_TASKS)
    finally:
        conn.close()


def test_foreign_keys_are_enabled(in_memory_settings: None) -> None:
    conn = db.connect()
    try:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conn.close()


def test_rows_are_addressable_by_column_name(in_memory_settings: None) -> None:
    conn = db.connect()
    try:
        db.init_db(conn)
        db.seed_tasks(conn)
        row = conn.execute("SELECT title, status FROM tasks LIMIT 1").fetchone()
        assert isinstance(row, sqlite3.Row)
        assert row["title"]
    finally:
        conn.close()
