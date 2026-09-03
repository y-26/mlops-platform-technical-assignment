# Project Walkthrough for Technical Review

## 1. What the project does

This project manages the operational part of the ML lifecycle after a model has been trained. A user can register a model, add versions, approve/promote a version, request a staging or production deployment, view monitoring metrics, retry a failed deployment and roll back a successful production deployment.

## 2. Request flow

`Angular UI → FastAPI endpoint → service/business rule → SQLAlchemy → PostgreSQL`

The API contracts are defined with Pydantic. SQLAlchemy models represent the persistent entities. Business rules such as lifecycle validation, production approval checks and idempotency are kept in `backend/app/services.py`.

## 3. Important backend files

- `backend/app/main.py`: REST endpoints, health endpoint and request logging.
- `backend/app/services.py`: lifecycle transition and deployment business rules.
- `backend/app/models.py`: database entities and enums.
- `backend/app/schemas.py`: request/response validation models.
- `backend/app/database.py`: SQLAlchemy engine/session setup.
- `backend/app/errors.py`: consistent domain/API errors.
- `backend/app/seed.py`: loads demo registry and monitoring data.

## 4. Lifecycle rule

The allowed path is `DRAFT → VALIDATED → APPROVED → STAGING → PRODUCTION → ARCHIVED`. The service rejects invalid jumps. Production deployment also requires approval status to be `APPROVED`.

## 5. Idempotency

Every deployment request contains an idempotency key. Before creating a deployment, the service checks whether that key already exists. If it does, the existing deployment is returned. This protects the system from duplicate deployments when a client retries the same request.

## 6. Retry

Only a `FAILED` deployment can be retried. The attempt counter is incremented, a retry event is added and the deployment workflow is executed again.

## 7. Rollback

Rollback is allowed only for a successful production deployment. In this assignment it records the rollback and archives the deployed version. In a real system the deployment adapter would restore the previous known-good production version.

## 8. Monitoring

The monitoring API returns latency, throughput, error rate, quality, drift and availability. A simple health rule marks the model degraded if error rate or drift crosses the configured logic in the endpoint, or availability falls below the threshold.

## 9. Why the deployment is simulated

The evaluator should be able to run the project without an Azure subscription or Kubernetes cluster. The local adapter demonstrates the workflow. In production I would make deployment asynchronous and replace it with an Azure ML/AKS integration.

## 10. CI/CD

GitHub Actions runs Ruff, Pytest/coverage, Angular tests/build and Docker Compose validation on pushes and pull requests.

## 11. Docker Compose

Docker Compose starts PostgreSQL first. The backend waits for the database health check, and the frontend waits for the backend health check. This provides a repeatable local environment.

## 12. Improvements I would make next

Add authentication/RBAC, asynchronous deployment workers, live Azure ML/AKS deployment integration, Prometheus/Azure Monitor metric ingestion, PostgreSQL integration tests and Playwright UI tests.
