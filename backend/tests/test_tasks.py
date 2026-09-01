"""Task listing tests: the list endpoint and its status filter."""

import pytest
from fastapi.testclient import TestClient

from app.db import SEED_TASKS


def test_list_returns_every_seeded_task(client: TestClient) -> None:
    response = client.get("/tasks")

    assert response.status_code == 200
    assert len(response.json()) == len(SEED_TASKS)


@pytest.mark.parametrize(
    ("status", "expected"),
    [("NEW", 3), ("IN_PROGRESS", 2), ("COMPLETED", 1)],
)
def test_filter_returns_only_matching_tasks(client: TestClient, status: str, expected: int) -> None:
    tasks = client.get("/tasks", params={"status": status}).json()

    assert len(tasks) == expected
    assert {task["status"] for task in tasks} == {status}


def test_filter_reflects_a_status_change(client: TestClient) -> None:
    assert len(client.get("/tasks", params={"status": "NEW"}).json()) == 3

    client.patch("/tasks/1/status", json={"status": "COMPLETED"})

    assert len(client.get("/tasks", params={"status": "NEW"}).json()) == 2
    assert len(client.get("/tasks", params={"status": "COMPLETED"}).json()) == 2


def test_unsupported_filter_value_is_rejected(client: TestClient) -> None:
    response = client.get("/tasks", params={"status": "ARCHIVED"})

    assert response.status_code == 422


def test_tasks_are_returned_newest_first(client: TestClient) -> None:
    dates = [task["createdAt"] for task in client.get("/tasks").json()]

    assert dates == sorted(dates, reverse=True)


def test_task_uses_the_documented_json_shape(client: TestClient) -> None:
    task = client.get("/tasks").json()[0]

    # The brief's examples are camelCase; snake_case must not leak onto the wire.
    assert set(task) == {
        "id",
        "title",
        "description",
        "priority",
        "status",
        "createdAt",
    }
