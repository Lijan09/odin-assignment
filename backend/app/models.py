"""Pydantic models and domain enums.

The assessment's JSON examples are camelCase (`createdAt`, `recommendedAction`), so
every model here derives from `CamelModel`: Python code stays snake_case while the
API emits and accepts the documented shape.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Status(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Category(str, Enum):
    """Categories the AI may assign, shaped around Odin's operations work."""

    DOCUMENT_REQUEST = "DOCUMENT_REQUEST"
    COMPLIANCE_CHECK = "COMPLIANCE_CHECK"
    CLIENT_FOLLOW_UP = "CLIENT_FOLLOW_UP"
    ESCALATION = "ESCALATION"


class CamelModel(BaseModel):
    """Base model: snake_case attributes, camelCase JSON.

    `populate_by_name` lets these models be built either way, which matters when
    parsing an LLM response that uses the camelCase keys from the prompt.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Task(CamelModel):
    id: int
    title: str
    description: str
    priority: Priority
    status: Status
    created_at: datetime


class StatusUpdate(CamelModel):
    """Body of PATCH /tasks/{id}/status.

    Typing this as the enum means an unsupported value is rejected before any
    handler code runs.
    """

    status: Status


class AnalysisResult(CamelModel):
    """Structured AI output, validated before it is returned to the client.

    The length caps are deliberate: this model parses text produced by a language
    model, so it is treated as untrusted input rather than trusted data.
    """

    category: Category
    priority: Priority
    summary: str = Field(min_length=1, max_length=500)
    recommended_action: str = Field(min_length=1, max_length=500)
