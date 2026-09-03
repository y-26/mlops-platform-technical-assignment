import csv
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import func, select
from app.database import Base, SessionLocal, engine
from app.models import ApprovalStatus, Environment, Metric, Model, ModelVersion, Stage


DATA = Path(__file__).resolve().parents[2] / "data"


def seed() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.scalar(select(func.count(Model.id))):
            registry = json.loads((DATA / "sample_model_registry.json").read_text())
            for raw in registry:
                model = Model(
                    id=raw["model_id"],
                    name=raw["name"],
                    owner=raw["owner"],
                    description=(
                        "Predicts healthy/unhealthy clutch condition"
                        if raw["model_id"] == "clutch-health-classifier"
                        else "Groups customers into behavioral segments"
                    ),
                    tags={"source": "assignment-seed"},
                )
                db.add(model)
                db.flush()
                for v in raw["versions"]:
                    db.add(
                        ModelVersion(
                            model_id=model.id,
                            version=v["version"],
                            framework=raw["framework"],
                            algorithm=(
                                "RandomForestClassifier"
                                if model.id == "clutch-health-classifier"
                                else "KMeans"
                            ),
                            artifact_uri=v["artifact_uri"],
                            training_data_ref=f"dataset://{model.id}/v1",
                            approval_status=ApprovalStatus.APPROVED
                            if v["approved"]
                            else ApprovalStatus.PENDING,
                            stage=Stage(v["stage"]),
                        )
                    )
            db.commit()

        if db.scalar(select(func.count(Metric.id))):
            return

        registered_model_ids = set(db.scalars(select(Model.id)).all())
        with (DATA / "sample_model_metrics.csv").open(newline="") as file:
            for row in csv.DictReader(file):
                if row["model_id"] not in registered_model_ids:
                    continue
                db.add(
                    Metric(
                        timestamp=datetime.fromisoformat(
                            row["timestamp"].replace("Z", "+00:00")
                        ),
                        model_id=row["model_id"],
                        version=row["version"],
                        environment=Environment(row["environment"]),
                        latency_ms=float(row["latency_ms"]),
                        throughput_rpm=float(row["throughput_rpm"]),
                        error_rate=float(row["error_rate"]),
                        quality_score=float(row["quality_score"]),
                        drift_score=float(row["drift_score"]),
                        availability=float(row["availability"]),
                    )
                )
        db.commit()


if __name__ == "__main__":
    seed()
