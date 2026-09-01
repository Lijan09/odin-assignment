"""The seam between the application and whatever produces an analysis.

Both the mock and the Gemini implementation satisfy `AiAnalyser`. Nothing outside
this package needs to know which one is in use, which is what makes the failure
path testable without a network or an API key.
"""

from typing import Protocol, runtime_checkable

from app.models import AnalysisResult


class AiAnalysisError(Exception):
    """Raised when an analysis could not be produced or could not be trusted.

    Covers every failure mode the caller should treat identically: the provider
    was unreachable, it returned nothing, or it returned something that did not
    validate against AnalysisResult. The web layer turns this into a 502.
    """


@runtime_checkable
class AiAnalyser(Protocol):
    """Structural interface for an analyser. No inheritance required."""

    def analyse(self, title: str, description: str) -> AnalysisResult:
        """Classify a task, or raise AiAnalysisError."""
        ...
