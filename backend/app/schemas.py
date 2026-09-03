from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models import ApprovalStatus, DeploymentStatus, Environment, Stage


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ModelCreate(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=64)
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    owner: str = Field(min_length=2, max_length=200)
    tags: dict[str, str] = Field(default_factory=dict)


class VersionCreate(BaseModel):
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")
    framework: str = Field(min_length=2, max_length=100)
    algorithm: str = Field(min_length=2, max_length=100)
    artifact_uri: str = Field(min_length=5, max_length=500)
    training_data_ref: str = Field(min_length=3, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("artifact_uri")
    @classmethod
    def validate_artifact_uri(cls, value: str) -> str:
        if "://" not in value:
            raise ValueError("artifact_uri must be an absolute URI")
        return value


class VersionUpdate(BaseModel):
    approval_status: ApprovalStatus | None = None
    stage: Stage | None = None


class VersionRead(ApiModel):
    id: int
    model_id: str
    version: str
    framework: str
    algorithm: str
    artifact_uri: str
    training_data_ref: str
    metadata: dict[str, Any] = Field(validation_alias="metadata_")
    approval_status: ApprovalStatus
    stage: Stage
    created_at: datetime
    updated_at: datetime


class ModelRead(ApiModel):
    id: str
    name: str
    description: str
    owner: str
    tags: dict[str, str]
    created_at: datetime
    updated_at: datetime
    versions: list[VersionRead] = []


class DeploymentCreate(BaseModel):
    model_id: str
    version: str
    environment: Environment
    idempotency_key: str = Field(min_length=8, max_length=100)
    simulate_failure: bool = False


class EventRead(ApiModel):
    id: int
    status: DeploymentStatus
    event: str
    detail: str | None
    created_at: datetime


class DeploymentRead(ApiModel):
    id: str
    model_id: str
    environment: Environment
    status: DeploymentStatus
    idempotency_key: str
    simulate_failure: bool
    attempt: int
    previous_deployment_id: str | None
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime
    events: list[EventRead] = []
    version: VersionRead


class MetricRead(ApiModel):
    timestamp: datetime
    model_id: str
    version: str
    environment: Environment
    latency_ms: float
    throughput_rpm: float
    error_rate: float
    quality_score: float
    drift_score: float
    availability: float


class MetricsResponse(BaseModel):
    items: list[MetricRead]
    monitoring_status: str
    last_successful_inference: datetime | None
