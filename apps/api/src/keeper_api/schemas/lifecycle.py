from pydantic import BaseModel, ConfigDict, Field

from keeper_api.models.statuses import AgentProfileStatus, CandidateStatus


class CandidateTransitionRequest(BaseModel):
    status: CandidateStatus
    reason: str | None = Field(default=None, max_length=1000)


class CandidateStatusResponse(BaseModel):
    status: CandidateStatus


class AgentTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: AgentProfileStatus
    reason: str | None = Field(default=None, max_length=1000)


class AgentStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: AgentProfileStatus
