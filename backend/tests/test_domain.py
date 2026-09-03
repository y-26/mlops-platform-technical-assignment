import pytest
from app.errors import DomainError
from app.models import ApprovalStatus, ModelVersion, Stage
from app.services import transition_version


def version(stage=Stage.DRAFT, approval=ApprovalStatus.PENDING):
    return ModelVersion(
        model_id="m",
        version="1.0.0",
        framework="x",
        algorithm="x",
        artifact_uri="s3://x",
        training_data_ref="d",
        stage=stage,
        approval_status=approval,
    )


def test_invalid_stage_transition_is_rejected():
    with pytest.raises(DomainError):
        transition_version(version(), Stage.PRODUCTION)


def test_approved_version_can_move_to_staging():
    item = version(Stage.APPROVED, ApprovalStatus.APPROVED)
    transition_version(item, Stage.STAGING)
    assert item.stage == Stage.STAGING
