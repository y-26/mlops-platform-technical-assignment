# Test Strategy

## Goal

The tests focus on the business rules that are most important for this assignment rather than only testing successful CRUD operations.

## Backend tests

The backend test suite uses Pytest and an isolated SQLite database. The main scenarios are:

- create a model and reject a duplicate model
- register a model version
- reject an invalid lifecycle transition
- prevent an unapproved version from being deployed to production
- allow an approved version to be deployed
- return the same deployment for a repeated idempotency key
- simulate a failed deployment
- retry a failed deployment successfully
- roll back a successful production deployment

Unit tests cover lifecycle rules directly. API tests exercise the complete request-to-database workflow.

## Frontend tests

Angular tests validate API integration and presentation logic without requiring the backend to be running. HTTP calls are mocked in the test environment.

## CI validation

GitHub Actions runs backend linting and Pytest with a coverage threshold. It also installs the frontend dependencies, runs Angular tests, builds the frontend and validates the Docker Compose configuration.

## Additional production tests

With more time I would add PostgreSQL integration tests using Testcontainers and browser-level tests using Playwright. For a real Azure deployment adapter I would also add contract tests around the Azure ML/AKS integration.
