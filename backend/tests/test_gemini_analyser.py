"""Unit tests for the Gemini analyser's failure handling.

These never reach the network: the SDK call is replaced with a stub that returns
a scripted sequence of responses and errors. What is under test is our retry
policy and, most importantly, that a model response is validated rather than
trusted.
"""

from typing import Any

import pytest
from google.genai import errors

from app.ai.base import AiAnalysisError
from app.ai.gemini import GeminiAnalyser

VALID_JSON = (
    '{"category":"DOCUMENT_REQUEST","priority":"HIGH",'
    '"summary":"Customer has not supplied a payslip.",'
    '"recommendedAction":"Request the missing payslip."}'
)


class ScriptedAnalyser(GeminiAnalyser):
    """A GeminiAnalyser whose single SDK call is replaced by a script.

    Overriding `_call_model` exercises the real retry and validation logic while
    never opening a socket.
    """

    def __init__(self, script: list[Any]) -> None:
        super().__init__(api_key="test-key", model="test-model", timeout_seconds=1.0)
        self._script = script
        self.calls = 0

    def _call_model(self, prompt: str) -> str | None:
        item = self._script[self.calls]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return item


def build(script: list[Any]) -> ScriptedAnalyser:
    return ScriptedAnalyser(script)


def analyse(analyser: ScriptedAnalyser):
    return analyser.analyse("Missing customer document", "No payslip provided.")


def test_valid_response_is_returned() -> None:
    analyser = build([VALID_JSON])

    result = analyse(analyser)

    assert result.category.value == "DOCUMENT_REQUEST"
    assert result.recommended_action == "Request the missing payslip."
    assert analyser.calls == 1


def test_server_error_is_retried_once_and_can_succeed() -> None:
    analyser = build([errors.ServerError(503, {"error": {}}), VALID_JSON])

    assert analyse(analyser).priority.value == "HIGH"
    assert analyser.calls == 2


def test_repeated_server_errors_raise_ai_analysis_error() -> None:
    analyser = build(
        [errors.ServerError(503, {"error": {}}), errors.ServerError(503, {"error": {}})]
    )

    with pytest.raises(AiAnalysisError):
        analyse(analyser)
    assert analyser.calls == 2


def test_client_error_is_not_retried() -> None:
    """A 4xx means a bad key or bad request; repeating it cannot help."""
    analyser = build([errors.ClientError(400, {"error": {}}), VALID_JSON])

    with pytest.raises(AiAnalysisError):
        analyse(analyser)
    assert analyser.calls == 1


def test_empty_response_is_retried() -> None:
    analyser = build(["", VALID_JSON])

    assert analyse(analyser).category.value == "DOCUMENT_REQUEST"
    assert analyser.calls == 2


def test_malformed_json_raises_ai_analysis_error() -> None:
    analyser = build(["not json at all", "still not json"])

    with pytest.raises(AiAnalysisError):
        analyse(analyser)


@pytest.mark.parametrize(
    "payload",
    [
        # Well-formed JSON that violates the contract in different ways.
        '{"category":"REFUND","priority":"HIGH","summary":"s","recommendedAction":"a"}',
        '{"category":"DOCUMENT_REQUEST","priority":"URGENT","summary":"s","recommendedAction":"a"}',
        '{"category":"DOCUMENT_REQUEST","priority":"HIGH","summary":"s"}',
        '{"category":"DOCUMENT_REQUEST","priority":"HIGH","summary":"","recommendedAction":"a"}',
    ],
)
def test_response_violating_the_schema_is_rejected(payload: str) -> None:
    """The heart of it: model output is validated, not trusted.

    The schema is sent with the request, but a response that slips past it must
    still fail here rather than reaching the caller.
    """
    analyser = build([payload, payload])

    with pytest.raises(AiAnalysisError):
        analyse(analyser)


def test_failure_message_does_not_leak_provider_detail() -> None:
    analyser = build(
        [
            errors.ServerError(503, {"error": {"message": "internal-host-42 exploded"}}),
            errors.ServerError(503, {"error": {"message": "internal-host-42 exploded"}}),
        ]
    )

    with pytest.raises(AiAnalysisError) as caught:
        analyse(analyser)

    assert "internal-host-42" not in str(caught.value)
