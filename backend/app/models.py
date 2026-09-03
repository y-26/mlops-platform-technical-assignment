import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Stage(str, enum.Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    ARCHIVED = "ARCHIVED"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Environment(str, enum.Enum):
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    VALIDATING = "VALIDATING"
    DEPLOYING = "DEPLOYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class Model(Base):
    __tablename__ = "models"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    owner: Mapped[str] = mapped_column(String(200))
    tags: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    versions: Mapped[list["ModelVersion"]] = relationship(
        back_populates="model", cascade="all, delete-orphan"
    )


class ModelVersion(Base):
    __tablename__ = "model_versions"
    __table_args__ = (UniqueConstraint("model_id", "version", name="uq_model_version"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id"), index=True)
    version: Mapped[str] = mapped_column(String(50))
    framework: Mapped[str] = mapped_column(String(100))
    algorithm: Mapped[str] = mapped_column(String(100))
    artifact_uri: Mapped[str] = mapped_column(String(500))
    training_data_ref: Mapped[str] = mapped_column(String(500))
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING
    )
    stage: Mapped[Stage] = mapped_column(Enum(Stage), default=Stage.DRAFT)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    model: Mapped[Model] = relationship(back_populates="versions")


class Deployment(Base):
    __tablename__ = "deployments"
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id"), index=True)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"))
    environment: Mapped[Environment] = mapped_column(Enum(Environment))
    status: Mapped[DeploymentStatus] = mapped_column(
        Enum(DeploymentStatus), default=DeploymentStatus.REQUESTED
    )
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True)
    simulate_failure: Mapped[bool] = mapped_column(Boolean, default=False)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    previous_deployment_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    version: Mapped[ModelVersion] = relationship()
    events: Mapped[list["DeploymentEvent"]] = relationship(
        back_populates="deployment",
        cascade="all, delete-orphan",
        order_by="DeploymentEvent.created_at",
    )


class DeploymentEvent(Base):
    __tablename__ = "deployment_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deployment_id: Mapped[str] = mapped_column(ForeignKey("deployments.id"), index=True)
    status: Mapped[DeploymentStatus] = mapped_column(Enum(DeploymentStatus))
    event: Mapped[str] = mapped_column(String(100))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    deployment: Mapped[Deployment] = relationship(back_populates="events")


class Metric(Base):
    __tablename__ = "metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id"), index=True)
    version: Mapped[str] = mapped_column(String(50))
    environment: Mapped[Environment] = mapped_column(Enum(Environment))
    latency_ms: Mapped[float] = mapped_column(Float)
    throughput_rpm: Mapped[float] = mapped_column(Float)
    error_rate: Mapped[float] = mapped_column(Float)
    quality_score: Mapped[float] = mapped_column(Float)
    drift_score: Mapped[float] = mapped_column(Float)
    availability: Mapped[float] = mapped_column(Float)
