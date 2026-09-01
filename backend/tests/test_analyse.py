"""AI analysis tests, including the designed failure path.

"AI failure is handled correctly" is the third behaviour the brief names. The
analyser is a FastAPI dependency, so these tests swap in a failing implementation
rather than patching internals or touching the network.
"""

import pytest
from fastapi.testclient import TestClient

from app.ai.base import AiAnalysisError
from app.ai.provider import get_analyser
from app.main import app
from app.models import AnalysisResult, Category, Priority


class FailingAnalyser:
    """An analyser that always fails, exactly as an unreachable provider would."""

    def analyse(self, title: str, description: str) -> AnalysisResult:
        raise AiAnalysisError("AI analysis is currently unavailable.")


class ExplodingAnalyser:
    """An analyser that raises something unexpected, not AiAnalysisError."""

    def analyse(self, title: str, description: str) -> AnalysisResult:
        raise RuntimeError("boom")


@pytest.fixture
def failing_client(client: TestClient) -> TestClient:
    """The standard client, but with an analyser that always fails."""
    app.dependency_overrides[get_analyser] = FailingAnalyser
    return client


def test_analysis_returns_the_documented_shape(client: TestClient) -> None:
    response = client.post("/tasks/1/analyse")

    assert response.status_code == 200
    body = response.json()
    # The brief's contract is camelCase and exactly these four fields.
    assert set(body) == {"category", "priority", "summary", "recommendedAction"}
    assert body["category"] in {c.value for c in Category}
    assert body["priority"] in {p.value for p in Priority}
    assert body["summary"] and body["recommendedAction"]


def test_analysis_of_the_briefs_example_task(client: TestClient) -> None:
    body = client.post("/tasks/1/analyse").json()

    assert body["category"] == "DOCUMENT_REQUEST"
    assert body["priority"] == "HIGH"


def test_analysis_does_not_modify_the_task(client: TestClient) -> None:
    before = client.get("/tasks").json()

    assert client.post("/tasks/1/analyse").status_code == 200

    assert client.get("/tasks").json() == before


def test_analysis_of_unknown_task_returns_404(client: TestClient) -> None:
    response = client.post("/tasks/999/analyse")

    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_ai_failure_returns_502(failing_client: TestClient) -> None:
    """The rubric case: the provider fails and the API reports it cleanly."""
    response = failing_client.post("/tasks/1/analyse")

    assert response.status_code == 502
    assert response.json() == {
        "error": "ai_unavailable",
        "message": "AI analysis is currently unavailable.",
    }


def test_ai_failure_does_not_crash_the_application(failing_client: TestClient) -> None:
    assert failing_client.post("/tasks/1/analyse").status_code == 502

    # The rest of the API keeps working after a provider failure.
    assert failing_client.get("/tasks").status_code == 200
    assert failing_client.patch("/tasks/1/status", json={"status": "COMPLETED"}).status_code == 200
    # And the failure is not sticky: a second attempt fails the same clean way.
    assert failing_client.post("/tasks/1/analyse").status_code == 502


def test_ai_failure_is_checked_after_the_task_exists(failing_client: TestClient) -> None:
    """An unknown id must 404 rather than 502: no provider call should be made."""
    assert failing_client.post("/tasks/999/analyse").status_code == 404


def test_unexpected_analyser_error_is_not_swallowed(client: TestClient) -> None:
    """Only AiAnalysisError maps to 502; anything else is a genuine bug.

    Masking an unexpected exception as a clean 502 would hide real defects, so it
    is deliberately left to surface as a server error.
    """
    app.dependency_overrides[get_analyser] = ExplodingAnalyser

    with pytest.raises(RuntimeError):
        client.post("/tasks/1/analyse")
