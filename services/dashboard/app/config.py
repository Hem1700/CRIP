"""Configuration for the Dashboard service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Dashboard service configuration."""

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "crip-local"
    NEO4J_DATABASE: str = "neo4j"

    DYNAMODB_ENDPOINT: str = "http://localhost:8080"
    S3_ENDPOINT: str = "http://localhost:4566"
    S3_BUCKET_REPORTS: str = "crip-reports"

    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
