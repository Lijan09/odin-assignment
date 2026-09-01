"""Shared pytest fixtures: a fresh in-memory database per test."""

import sqlite3
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.ai.mock import MockAnalyser
from app.ai.provider import get_analyser
from app.db import get_connection, init_db, seed_tasks
from app.main import app


@pytest.fixture
def connection() -> Iterator[sqlite3.Connection]:
    """A fresh, seeded in-memory database scoped to a single test.

    Each test gets its own database, so no test can observe another's writes and
    none of them touch the developer's real odin_tasks.db file.
    """
    # check_same_thread=False is needed only here, not in production. FastAPI runs
    # sync endpoints in a threadpool, so a connection shared across requests is used
    # from a different thread than the one that created it. app.db.connect() is
    # exempt because it opens a connection inside the request itself. TestClient
    # issues requests sequentially, so this shared connection is never used
    # concurrently.
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    seed_tasks(conn)
    conn.commit()
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def client(connection: sqlite3.Connection) -> Iterator[TestClient]:
    """A TestClient wired to the in-memory database.

    Two details matter here:

    An in-memory database exists only for the lifetime of its connection, so the
    override yields the connection the fixture already opened. Calling connect()
    again would hand each request a different, empty database.

    TestClient is deliberately not used as a context manager. That would run the
    app's lifespan, which bootstraps and seeds the real on-disk database as a side
    effect of running the tests.
    """

    def override_get_connection() -> Iterator[sqlite3.Connection]:
        yield connection
        connection.commit()

    app.dependency_overrides[get_connection] = override_get_connection
    # Always analyse with the mock, whatever AI_PROVIDER says locally. Without
    # this, running the suite with a real key configured would make live, billable
    # API calls, and CI (which has no key) would fail. Tests that need a failure
    # override this again.
    app.dependency_overrides[get_analyser] = MockAnalyser
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
