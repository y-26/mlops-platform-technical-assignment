MODEL = {
    "id": "clutch-health-classifier",
    "name": "Clutch Health Classifier",
    "owner": "AI Team",
    "description": "Clutch health classification model",
    "tags": {"use_case": "predictive-maintenance"},
}
VERSION = {
    "version": "1.0.0",
    "framework": "scikit-learn",
    "algorithm": "random-forest",
    "artifact_uri": "models://clutch/1.0.0/model.pkl",
    "training_data_ref": "dataset://clutch/v4",
    "metadata": {},
}


def setup_version(client):
    assert client.post("/models", json=MODEL).status_code == 201
    assert client.post("/models/clutch-health-classifier/versions", json=VERSION).status_code == 201


def test_register_model_and_duplicate(client):
    assert client.post("/models", json=MODEL).status_code == 201
    response = client.post("/models", json=MODEL)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "MODEL_ALREADY_EXISTS"


def test_unapproved_version_cannot_go_to_production(client):
    setup_version(client)
    response = client.post(
        "/deployments",
        json={
            "model_id": "clutch-health-classifier",
            "version": "1.0.0",
            "environment": "production",
            "idempotency_key": "request-123",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "APPROVAL_REQUIRED"


def test_approved_deployment_is_idempotent(client):
    setup_version(client)
    assert (
        client.patch(
            "/models/clutch-health-classifier/versions/1.0.0", json={"approval_status": "APPROVED"}
        ).status_code
        == 200
    )
    payload = {
        "model_id": "clutch-health-classifier",
        "version": "1.0.0",
        "environment": "production",
        "idempotency_key": "request-456",
    }
    first = client.post("/deployments", json=payload)
    second = client.post("/deployments", json=payload)
    assert first.status_code == 202 and second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["status"] == "SUCCEEDED"


def test_failed_deployment_retry_and_rollback(client):
    setup_version(client)
    client.patch(
        "/models/clutch-health-classifier/versions/1.0.0", json={"approval_status": "APPROVED"}
    )
    result = client.post(
        "/deployments",
        json={
            "model_id": "clutch-health-classifier",
            "version": "1.0.0",
            "environment": "production",
            "idempotency_key": "request-789",
            "simulate_failure": True,
        },
    )
    assert result.json()["status"] == "FAILED"
    retried = client.post(f"/deployments/{result.json()['id']}/retry")
    assert retried.json()["status"] == "SUCCEEDED" and retried.json()["attempt"] == 2
    rolled = client.post(f"/deployments/{result.json()['id']}/rollback")
    assert rolled.json()["status"] == "ROLLED_BACK"


def test_health_and_missing_model_errors(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    missing = client.get("/models/does-not-exist")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "MODEL_NOT_FOUND"


def test_retry_is_rejected_for_successful_deployment(client):
    setup_version(client)
    client.patch(
        "/models/clutch-health-classifier/versions/1.0.0",
        json={"approval_status": "APPROVED"},
    )
    result = client.post(
        "/deployments",
        json={
            "model_id": "clutch-health-classifier",
            "version": "1.0.0",
            "environment": "production",
            "idempotency_key": "successful-deployment-1",
        },
    )
    retry = client.post(f"/deployments/{result.json()['id']}/retry")
    assert retry.status_code == 409
    assert retry.json()["error"]["code"] == "RETRY_NOT_ALLOWED"


def test_metrics_for_unknown_model_returns_404(client):
    response = client.get("/models/unknown-model/metrics")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MODEL_NOT_FOUND"
