# MLOps Model Lifecycle Platform — G13 Technical Assignment

This project implements a small MLOps platform for managing machine-learning models from registration through production deployment and monitoring. The main goal is to demonstrate model lifecycle management, deployment controls, persistence, testing and an operational UI rather than model training.

## Features

- Register ML models and model versions
- Store framework, algorithm, artifact URI, training-data reference and tags
- Approve model versions and control lifecycle promotion
- Prevent unapproved versions from being deployed to production
- Create staging and production deployments
- Avoid duplicate deployments using an idempotency key
- Simulate deployment failure, retry failed deployments and roll back production deployments
- View latency, throughput, error rate, quality, drift and availability metrics
- Keep deployment events for audit/history

## Technology stack

- **Frontend:** Angular
- **Backend:** FastAPI, Pydantic and SQLAlchemy
- **Database:** PostgreSQL
- **Database migrations:** Alembic
- **Testing:** Pytest and Angular/Jasmine tests
- **Packaging:** Docker and Docker Compose
- **CI:** GitHub Actions

## Quick start

Prerequisite: Docker Desktop with Docker Compose.

```bash
docker compose up --build
```

After the containers are healthy:

- Angular UI: `http://localhost:4200`
- FastAPI Swagger: `http://localhost:8000/docs`
- Health endpoint: `http://localhost:8000/health`

Sample registry and monitoring data are loaded into PostgreSQL when the application starts for the first time.

## Application flow

The main workflow implemented in the project is:

```text
Register Model
     ↓
Register Version
     ↓
Validate / Approve
     ↓
Deploy to Staging or Production
     ↓
Monitor Deployment
     ↓
Retry on Failure / Rollback Production
```

A model version follows the lifecycle:

```text
DRAFT → VALIDATED → APPROVED → STAGING → PRODUCTION → ARCHIVED
```

Production deployment has an additional approval check. This prevents a version with `PENDING` or `REJECTED` approval status from being promoted directly to production.

## Example API workflow

The example below uses a clutch-health classification model, similar to an industrial predictive-maintenance use case.

```bash
curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{"id":"clutch-health-classifier","name":"Clutch Health Classifier","owner":"ML Engineering","tags":{"use_case":"predictive-maintenance"}}'

curl -X POST http://localhost:8000/models/clutch-health-classifier/versions \
  -H "Content-Type: application/json" \
  -d '{"version":"1.0.0","framework":"scikit-learn","algorithm":"RandomForestClassifier","artifact_uri":"models://clutch/1.0.0/model.pkl","training_data_ref":"dataset://clutch/v4"}'

curl -X PATCH http://localhost:8000/models/clutch-health-classifier/versions/1.0.0 \
  -H "Content-Type: application/json" \
  -d '{"approval_status":"APPROVED"}'

curl -X POST http://localhost:8000/deployments \
  -H "Content-Type: application/json" \
  -d '{"model_id":"clutch-health-classifier","version":"1.0.0","environment":"production","idempotency_key":"clutch-production-1"}'
```

Reusing the same idempotency key returns the existing deployment instead of creating a duplicate. A failure can be tested using `"simulate_failure": true`, followed by `POST /deployments/{id}/retry`. A successful production deployment can be rolled back using `POST /deployments/{id}/rollback`.

## Local development and tests

### Backend

```bash
cd backend
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest --cov=app --cov-report=term-missing
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
npm test
npm run build
```

Configuration is environment-based. Copy `.env.example` when local overrides are required.

## Design choices

Business rules are kept in the backend service layer instead of the Angular application. This ensures that lifecycle and approval rules are applied even when the API is called directly.

The assignment uses a synchronous deployment simulator so the complete workflow can run locally without requiring an actual Kubernetes or cloud ML environment. In a production implementation, this deployment component could be replaced by an asynchronous worker that invokes Azure ML/AKS or another model-serving platform while keeping the API contract unchanged.

PostgreSQL is used for persistent model, deployment, event and monitoring records. The automated tests use an isolated test database so workflow behavior can be validated without depending on the running application.

## Documentation

- `docs/architecture.md` — application architecture and component responsibilities
- `docs/test-strategy.md` — testing approach and important scenarios
- `docs/adr/001-synchronous-deployment-adapter.md` — why deployment is simulated synchronously
- `docs/known-limitations.md` — current limitations and possible production improvements
- `docs/architecture-diagram.png` — exported architecture diagram

## Verification

The backend test suite contains nine tests covering model registration, duplicate handling, lifecycle rules, production approval, idempotency, failure/retry, rollback, health and missing resources. Run all local checks using the commands above. The repository also contains a GitHub Actions workflow for repeatable CI verification.

Runtime screenshots should be captured from the candidate's own machine after the final Docker Compose verification and placed under `docs/screenshots/`.
