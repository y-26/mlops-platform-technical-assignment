from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.errors import DomainError
from app.models import (
    ApprovalStatus,
    Deployment,
    DeploymentEvent,
    DeploymentStatus,
    Environment,
    ModelVersion,
    Stage,
)
from app.schemas import DeploymentCreate


ALLOWED_STAGE_TRANSITIONS = {
    Stage.DRAFT: {Stage.VALIDATED, Stage.ARCHIVED},
    Stage.VALIDATED: {Stage.APPROVED, Stage.DRAFT, Stage.ARCHIVED},
    Stage.APPROVED: {Stage.STAGING, Stage.ARCHIVED},
    Stage.STAGING: {Stage.PRODUCTION, Stage.APPROVED, Stage.ARCHIVED},
    Stage.PRODUCTION: {Stage.ARCHIVED},
    Stage.ARCHIVED: set(),
}


def transition_version(version: ModelVersion, target: Stage) -> None:
    if target == version.stage:
        return
    if target not in ALLOWED_STAGE_TRANSITIONS[version.stage]:
        raise DomainError(
            "INVALID_STAGE_TRANSITION",
            f"Cannot move {version.stage.value} to {target.value}",
            409,
        )
    if (
        target in {Stage.APPROVED, Stage.STAGING, Stage.PRODUCTION}
        and version.approval_status != ApprovalStatus.APPROVED
    ):
        raise DomainError(
            "APPROVAL_REQUIRED", "Version must be approved before promotion", 409
        )
    version.stage = target


def add_event(
    deployment: Deployment,
    status: DeploymentStatus,
    event: str,
    detail: str | None = None,
) -> None:
    deployment.status = status
    deployment.events.append(DeploymentEvent(status=status, event=event, detail=detail))


def execute_deployment(deployment: Deployment) -> None:
    add_event(deployment, DeploymentStatus.VALIDATING, "approval_validated")
    add_event(deployment, DeploymentStatus.DEPLOYING, "deployment_started")
    if deployment.simulate_failure:
        deployment.failure_reason = "Simulated runtime timeout"
        add_event(
            deployment,
            DeploymentStatus.FAILED,
            "runtime_timeout",
            deployment.failure_reason,
        )
    else:
        add_event(deployment, DeploymentStatus.SUCCEEDED, "deployment_completed")
        deployment.version.stage = (
            Stage.PRODUCTION
            if deployment.environment == Environment.PRODUCTION
            else Stage.STAGING
        )


def create_deployment(
    db: Session, request: DeploymentCreate
) -> tuple[Deployment, bool]:
    existing = db.scalar(
        select(Deployment)
        .where(Deployment.idempotency_key == request.idempotency_key)
        .options(selectinload(Deployment.events), selectinload(Deployment.version))
    )
    if existing:
        return existing, False
    version = db.scalar(
        select(ModelVersion).where(
            ModelVersion.model_id == request.model_id,
            ModelVersion.version == request.version,
        )
    )
    if not version:
        raise DomainError("VERSION_NOT_FOUND", "Model version was not found", 404)
    if (
        request.environment == Environment.PRODUCTION
        and version.approval_status != ApprovalStatus.APPROVED
    ):
        raise DomainError(
            "APPROVAL_REQUIRED",
            "Only approved versions can be deployed to production",
            409,
        )
    previous_deployment_id = None
    if request.environment == Environment.PRODUCTION:
        previous = db.scalar(
            select(Deployment)
            .where(
                Deployment.model_id == request.model_id,
                Deployment.environment == Environment.PRODUCTION,
                Deployment.status == DeploymentStatus.SUCCEEDED,
            )
            .order_by(Deployment.created_at.desc())
        )
        previous_deployment_id = previous.id if previous else None

    deployment = Deployment(
        model_id=request.model_id,
        model_version_id=version.id,
        version=version,
        environment=request.environment,
        idempotency_key=request.idempotency_key,
        simulate_failure=request.simulate_failure,
        previous_deployment_id=previous_deployment_id,
    )
    add_event(deployment, DeploymentStatus.REQUESTED, "deployment_requested")
    execute_deployment(deployment)
    db.add(deployment)
    db.commit()
    db.refresh(deployment)
    return deployment, True
