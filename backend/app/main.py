import logging
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from app.config import get_settings
from app.database import Base, engine, get_db
from app.errors import DomainError, install_error_handlers
from app.models import (
    ApprovalStatus,
    Deployment,
    DeploymentStatus,
    Metric,
    Model,
    ModelVersion,
    Stage,
)
from app.schemas import (
    DeploymentCreate,
    DeploymentRead,
    MetricsResponse,
    ModelCreate,
    ModelRead,
    VersionCreate,
    VersionRead,
    VersionUpdate,
)
from app.services import (
    add_event,
    create_deployment,
    execute_deployment,
    transition_version,
)

logger = logging.getLogger("mlops")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_error_handlers(app)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    logger.info(
        "request_complete",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    )
    return response


@app.get("/health", tags=["operability"])
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "healthy", "service": "api", "version": app.version}


@app.post("/models", response_model=ModelRead, status_code=201, tags=["registry"])
def register_model(body: ModelCreate, db: Session = Depends(get_db)):
    model = Model(**body.model_dump())
    db.add(model)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DomainError(
            "MODEL_ALREADY_EXISTS", "A model with this id or name already exists", 409
        )
    db.refresh(model)
    return model


@app.get("/models", response_model=list[ModelRead], tags=["registry"])
def list_models(
    q: str | None = Query(None), owner: str | None = None, db: Session = Depends(get_db)
):
    stmt = (
        select(Model)
        .options(selectinload(Model.versions))
        .order_by(Model.updated_at.desc())
    )
    if q:
        stmt = stmt.where(or_(Model.id.contains(q), Model.name.contains(q)))
    if owner:
        stmt = stmt.where(Model.owner == owner)
    return db.scalars(stmt).unique().all()


@app.get("/models/{model_id}", response_model=ModelRead, tags=["registry"])
def get_model(model_id: str, db: Session = Depends(get_db)):
    model = db.scalar(
        select(Model).where(Model.id == model_id).options(selectinload(Model.versions))
    )
    if not model:
        raise DomainError("MODEL_NOT_FOUND", "Model was not found", 404)
    return model


@app.post(
    "/models/{model_id}/versions",
    response_model=VersionRead,
    status_code=201,
    tags=["registry"],
)
def register_version(model_id: str, body: VersionCreate, db: Session = Depends(get_db)):
    if not db.get(Model, model_id):
        raise DomainError("MODEL_NOT_FOUND", "Model was not found", 404)
    version = ModelVersion(
        model_id=model_id,
        metadata_=body.metadata,
        **body.model_dump(exclude={"metadata"}),
    )
    db.add(version)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DomainError(
            "VERSION_ALREADY_EXISTS", "This semantic version is already registered", 409
        )
    db.refresh(version)
    return version


@app.get(
    "/models/{model_id}/versions", response_model=list[VersionRead], tags=["registry"]
)
def list_versions(model_id: str, db: Session = Depends(get_db)):
    if not db.get(Model, model_id):
        raise DomainError("MODEL_NOT_FOUND", "Model was not found", 404)
    return db.scalars(
        select(ModelVersion)
        .where(ModelVersion.model_id == model_id)
        .order_by(ModelVersion.created_at.desc())
    ).all()


@app.patch(
    "/models/{model_id}/versions/{version}",
    response_model=VersionRead,
    tags=["registry"],
)
def update_version(
    model_id: str, version: str, body: VersionUpdate, db: Session = Depends(get_db)
):
    item = db.scalar(
        select(ModelVersion).where(
            ModelVersion.model_id == model_id, ModelVersion.version == version
        )
    )
    if not item:
        raise DomainError("VERSION_NOT_FOUND", "Model version was not found", 404)
    if body.approval_status is not None:
        item.approval_status = body.approval_status
        if (
            body.approval_status == ApprovalStatus.APPROVED
            and item.stage == Stage.VALIDATED
        ):
            item.stage = Stage.APPROVED
    if body.stage is not None:
        transition_version(item, body.stage)
    db.commit()
    db.refresh(item)
    return item


@app.post(
    "/deployments", response_model=DeploymentRead, status_code=202, tags=["deployments"]
)
def request_deployment(
    body: DeploymentCreate, response: Response, db: Session = Depends(get_db)
):
    deployment, created = create_deployment(db, body)
    response.status_code = 202 if created else 200
    return deployment


@app.get("/deployments", response_model=list[DeploymentRead], tags=["deployments"])
def list_deployments(
    status: DeploymentStatus | None = None,
    model_id: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = (
        select(Deployment)
        .options(selectinload(Deployment.events), selectinload(Deployment.version))
        .order_by(Deployment.created_at.desc())
    )
    if status:
        stmt = stmt.where(Deployment.status == status)
    if model_id:
        stmt = stmt.where(Deployment.model_id == model_id)
    return db.scalars(stmt).unique().all()


def deployment_or_404(deployment_id: str, db: Session) -> Deployment:
    item = db.scalar(
        select(Deployment)
        .where(Deployment.id == deployment_id)
        .options(selectinload(Deployment.events), selectinload(Deployment.version))
    )
    if not item:
        raise DomainError("DEPLOYMENT_NOT_FOUND", "Deployment was not found", 404)
    return item


@app.get(
    "/deployments/{deployment_id}", response_model=DeploymentRead, tags=["deployments"]
)
def get_deployment(deployment_id: str, db: Session = Depends(get_db)):
    return deployment_or_404(deployment_id, db)


@app.post(
    "/deployments/{deployment_id}/retry",
    response_model=DeploymentRead,
    tags=["deployments"],
)
def retry_deployment(deployment_id: str, db: Session = Depends(get_db)):
    item = deployment_or_404(deployment_id, db)
    if item.status != DeploymentStatus.FAILED:
        raise DomainError(
            "RETRY_NOT_ALLOWED", "Only failed deployments can be retried", 409
        )
    item.attempt += 1
    item.simulate_failure = False
    item.failure_reason = None
    add_event(
        item, DeploymentStatus.REQUESTED, "retry_requested", f"Attempt {item.attempt}"
    )
    execute_deployment(item)
    db.commit()
    db.refresh(item)
    return item


@app.post(
    "/deployments/{deployment_id}/rollback",
    response_model=DeploymentRead,
    tags=["deployments"],
)
def rollback_deployment(deployment_id: str, db: Session = Depends(get_db)):
    item = deployment_or_404(deployment_id, db)
    if (
        item.environment.value != "production"
        or item.status != DeploymentStatus.SUCCEEDED
    ):
        raise DomainError(
            "ROLLBACK_NOT_ALLOWED",
            "Only a successful production deployment can be rolled back",
            409,
        )
    item.version.stage = Stage.ARCHIVED
    detail = "Deployment rolled back"
    if item.previous_deployment_id:
        previous = deployment_or_404(item.previous_deployment_id, db)
        previous.version.stage = Stage.PRODUCTION
        detail = f"Restored previous production deployment {previous.id}"
    add_event(item, DeploymentStatus.ROLLED_BACK, "rollback_completed", detail)
    db.commit()
    db.refresh(item)
    return item


@app.get(
    "/models/{model_id}/metrics", response_model=MetricsResponse, tags=["monitoring"]
)
def model_metrics(
    model_id: str,
    version: str | None = None,
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    if not db.get(Model, model_id):
        raise DomainError("MODEL_NOT_FOUND", "Model was not found", 404)
    stmt = (
        select(Metric)
        .where(Metric.model_id == model_id)
        .order_by(Metric.timestamp.desc())
        .limit(limit)
    )
    if version:
        stmt = stmt.where(Metric.version == version)
    items = list(reversed(db.scalars(stmt).all()))
    latest = items[-1] if items else None
    unhealthy = latest and (
        latest.error_rate > 0.05 or latest.drift_score > 0.3 or latest.availability < 99
    )
    return {
        "items": items,
        "monitoring_status": "DEGRADED"
        if unhealthy
        else ("HEALTHY" if latest else "NO_DATA"),
        "last_successful_inference": latest.timestamp if latest else None,
    }
