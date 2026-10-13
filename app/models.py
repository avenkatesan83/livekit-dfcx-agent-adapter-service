from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class A2APart(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    data: Any | None = None
    text: str | None = None
    media_type: str | None = Field(default=None, alias="mediaType")


class A2AMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    message_id: str = Field(alias="messageId")
    role: Literal["ROLE_USER", "ROLE_AGENT"]
    parts: list[A2APart] = Field(min_length=1)
    context_id: str | None = Field(default=None, alias="contextId")
    task_id: str | None = Field(default=None, alias="taskId")
    metadata: dict[str, Any] = Field(default_factory=dict)


class SendMessageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    message: A2AMessage
    configuration: dict[str, Any] | None = None


class UserContext(BaseModel):
    model_config = ConfigDict(extra="allow")

    ani: str | None = None
    caller_name: str | None = None
    authenticated: bool = False


class HandoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    handoff_version: Literal["1"]
    source: str
    session_id: str
    capability: str
    # Raw caller text used as the Dialogflow CX query; capability only selects the skill agent.
    utterance: str | None = None
    user_context: UserContext


class DFCXSkillAgent(BaseModel):
    """A single downstream Dialogflow CX agent this adapter can route to."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    capabilities: list[str] = Field(min_length=1)
    project_id: str = ""
    agent_id: str = ""
    location: str = "global"
    environment: str = "draft"
    language_code: str = "en-US"
    enabled: bool = True

    @field_validator("capabilities")
    @classmethod
    def normalize_capabilities(cls, values: list[str]) -> list[str]:
        normalized = [" ".join(value.strip().lower().split()) for value in values]
        if len(normalized) != len(set(normalized)):
            raise ValueError("capabilities must be unique per skill agent")
        return normalized
