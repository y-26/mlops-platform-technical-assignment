# ADR-001: Simulated synchronous deployment

## Status
Accepted for this assignment.

## Problem
A real model deployment can take several minutes and normally involves an external serving platform such as Azure ML, AKS or another Kubernetes-based runtime. Requiring that infrastructure would make the assignment difficult to run locally.

## Decision
The application simulates the deployment inside the backend. It still records the important states (`REQUESTED`, `VALIDATING`, `DEPLOYING`, `SUCCEEDED`/`FAILED`) and stores deployment events in the database.

## Why I chose this approach
It allows the evaluator to test approval validation, failure handling, retry, rollback and idempotency using only Docker Compose. The business workflow is separated from the actual cloud deployment mechanism, so the simulator can later be replaced by an Azure ML/AKS adapter.

## Trade-off
This does not represent the asynchronous behavior of a real production deployment. In production I would move deployment execution to a background worker/queue and keep the API responsible for creating and tracking the deployment request.
