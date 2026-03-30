"""Configuration for the Ingestion service, loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Ingestion service configuration.

    All values have local-dev defaults so the service starts without any .env file
    when docker-compose infrastructure is running.
    """

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "crip-local"
    NEO4J_DATABASE: str = "neo4j"

    AWS_REGION: str = "us-east-1"
    DYNAMODB_ENDPOINT: str = "http://localhost:8000"
    S3_ENDPOINT: str = "http://localhost:4566"

    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
