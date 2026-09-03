from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MLOps Control Plane"
    database_url: str = "sqlite:///./mlops.db"
    cors_origins: str = "http://localhost:4200,http://localhost"
    log_level: str = "INFO"
    seed_demo_data: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
