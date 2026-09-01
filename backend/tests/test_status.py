"""Status update tests: a valid status is accepted, an invalid one is rejected.

These are two of the three behaviours the assessment brief names. The third, AI
failure handling, lives in test_analyse.py.
"""

import pytest
from fastapi.testclient import TestClient

from app.models import Status


def read_task(client: TestClient, task_id: int) -> dict:
    """Fetch one task through the API, so assertions check what a client would see."""
    tasks = client.get("/tasks").json()
    return next(task for task in tasks if task["id"] == task_id)


@pytest.mark.parametrize("status", [s.value for s in Status])
def test_every_supported_status_is_accepted(client: TestClient, status: str) -> None:
    response = client.patch("/tasks/1/status", json={"status": status})

    assert response.status_code == 200
    assert response.json()["status"] == status


def test_valid_status_change_is_persisted(client: TestClient) -> None:
    assert read_task(client, 1)["status"] == "NEW"

    response = client.patch("/tasks/1/status", json={"status": "IN_PROGRESS"})
    assert response.status_code == 200

    # Re-read through a separate request rather than trusting the response body.
    # This is what distinguishes a real write from an echoed payload.
    assert read_task(client, 1)["status"] == "IN_PROGRESS"


@pytest.mark.parametrize(
    "value",
    [
        "ARCHIVED",  # not a member of the enum
        "in_progress",  # right value, wrong case
        "",  # empty string
        5,  # wrong JSON type
        None,  # explicit null
    ],
)
def test_unsupported_status_is_rejected(client: TestClient, value: object) -> None:
    response = client.patch("/tasks/1/status", json={"status": value})

    assert response.status_code == 422


def test_rejected_status_leaves_the_task_unchanged(client: TestClient) -> None:
    before = read_task(client, 1)

    response = client.patch("/tasks/1/status", json={"status": "ARCHIVED"})
    assert response.status_code == 422

    # A rejected request must not partially apply.
    assert read_task(client, 1) == before


def test_missing_status_field_is_rejected(client: TestClient) -> None:
    response = client.patch("/tasks/1/status", json={})

    assert response.status_code == 422


def test_rejection_body_has_the_documented_shape(client: TestClient) -> None:
    response = client.patch("/tasks/1/status", json={"status": "ARCHIVED"})

    body = response.json()
    assert body["error"] == "validation_error"
    assert body["details"][0]["field"] == "status"
    # The message names the values the caller may use.
    assert "NEW" in body["details"][0]["message"]


def test_unknown_task_returns_404(client: TestClient) -> None:
    response = client.patch("/tasks/999/status", json={"status": "COMPLETED"})

    assert response.status_code == 404
    assert response.json() == {
        "error": "not_found",
        "message": "Task 999 was not found.",
    }


def test_non_integer_task_id_is_rejected(client: TestClient) -> None:
    response = client.patch("/tasks/abc/status", json={"status": "NEW"})

    assert response.status_code == 422
