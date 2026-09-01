"""A deterministic analyser used for local runs, tests and CI.

The brief explicitly permits a mock AI service. This one is keyword-based rather
than random so its output is reproducible: the same task always yields the same
analysis, which is what makes it usable as a test fixture.
"""

from app.models import AnalysisResult, Category, Priority

# Ordered most specific first: the first category whose keywords appear wins.
_CATEGORY_KEYWORDS: tuple[tuple[Category, tuple[str, ...]], ...] = (
    (
        Category.DOCUMENT_REQUEST,
        ("payslip", "document", "statement", "paperwork", "upload", "provide"),
    ),
    (
        Category.COMPLIANCE_CHECK,
        ("verification", "certified", "identity", "passport", "compliance", "aml"),
    ),
    (
        Category.ESCALATION,
        ("urgent", "escalate", "overdue", "settlement", "deadline", "complaint"),
    ),
    (
        Category.CLIENT_FOLLOW_UP,
        ("follow", "chase", "asked", "query", "question", "response"),
    ),
)

_HIGH_SIGNALS = (
    "urgent",
    "immediately",
    "overdue",
    "settlement",
    "will not",
    "deadline",
    "missing",
    "has not provided",
    "outstanding",
)
_LOW_SIGNALS = ("no response", "awaiting", "when convenient", "routine")

_ACTIONS: dict[Category, str] = {
    Category.DOCUMENT_REQUEST: "Request the missing document from the customer.",
    Category.COMPLIANCE_CHECK: "Complete the outstanding verification check.",
    Category.ESCALATION: "Escalate to the responsible broker for a decision.",
    Category.CLIENT_FOLLOW_UP: "Follow up with the client and confirm next steps.",
}


def _classify(text: str) -> Category:
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return category
    return Category.CLIENT_FOLLOW_UP


def _prioritise(text: str) -> Priority:
    if any(signal in text for signal in _HIGH_SIGNALS):
        return Priority.HIGH
    if any(signal in text for signal in _LOW_SIGNALS):
        return Priority.LOW
    return Priority.MEDIUM


def _summarise(title: str, description: str) -> str:
    """First sentence of the description, falling back to the title."""
    first = description.strip().split(". ")[0].strip().rstrip(".")
    summary = f"{first}." if first else title.strip()
    return summary[:500]


class MockAnalyser:
    """Keyword-driven stand-in for a language model."""

    def analyse(self, title: str, description: str) -> AnalysisResult:
        haystack = f"{title} {description}".lower()
        category = _classify(haystack)
        return AnalysisResult(
            category=category,
            priority=_prioritise(haystack),
            summary=_summarise(title, description),
            recommended_action=_ACTIONS[category],
        )
