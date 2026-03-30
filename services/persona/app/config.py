"""Configuration for the Persona service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Persona service configuration."""

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "crip-local"
    NEO4J_DATABASE: str = "neo4j"

    ANTHROPIC_API_KEY: str = ""
    DYNAMODB_ENDPOINT: str = "http://localhost:8000"
    CONFIDENCE_THRESHOLD: float = 0.85

    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
