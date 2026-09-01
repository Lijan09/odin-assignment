"""Priority update tests, mirroring the status update rules.

Priority is editable in addition to status. The AI's suggested priority stays
advisory: nothing writes it automatically, an operator chooses to apply it.
"""

import pytest
from fastapi.testclient import TestClient

from app.models import Priority


def read_task(client: TestClient, task_id: int) -> dict:
    tasks = client.get("/tasks").json()
    return next(task for task in tasks if task["id"] == task_id)


@pytest.mark.parametrize("priority", [p.value for p in Priority])
def test_every_supported_priority_is_accepted(client: TestClient, priority: str) -> None:
    response = client.patch("/tasks/1/priority", json={"priority": priority})

    assert response.status_code == 200
    assert response.json()["priority"] == priority


def test_valid_priority_change_is_persisted(client: TestClient) -> None:
    assert read_task(client, 1)["priority"] == "HIGH"

    assert client.patch("/tasks/1/priority", json={"priority": "LOW"}).status_code == 200

    assert read_task(client, 1)["priority"] == "LOW"


@pytest.mark.parametrize("value", ["URGENT", "high", "", 5, None])
def test_unsupported_priority_is_rejected(client: TestClient, value: object) -> None:
    response = client.patch("/tasks/1/priority", json={"priority": value})

    assert response.status_code == 422


def test_rejected_priority_leaves_the_task_unchanged(client: TestClient) -> None:
    before = read_task(client, 1)

    assert client.patch("/tasks/1/priority", json={"priority": "URGENT"}).status_code == 422

    assert read_task(client, 1) == before


def test_unknown_task_returns_404(client: TestClient) -> None:
    response = client.patch("/tasks/999/priority", json={"priority": "LOW"})

    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_priority_change_does_not_touch_status(client: TestClient) -> None:
    """The two fields are independent; editing one must not disturb the other."""
    before = read_task(client, 1)

    client.patch("/tasks/1/priority", json={"priority": "LOW"})

    after = read_task(client, 1)
    assert after["status"] == before["status"]
    assert after["title"] == before["title"]
    assert after["createdAt"] == before["createdAt"]


def test_status_change_does_not_touch_priority(client: TestClient) -> None:
    before = read_task(client, 1)

    client.patch("/tasks/1/status", json={"status": "COMPLETED"})

    assert read_task(client, 1)["priority"] == before["priority"]
