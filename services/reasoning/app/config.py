"""Configuration for the Reasoning service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Reasoning service configuration."""

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "crip-local"
    NEO4J_DATABASE: str = "neo4j"

    ANTHROPIC_API_KEY: str = ""
    BEDROCK_REGION: str = "us-east-1"
    USE_BEDROCK: bool = False
    LLM_MODEL: str = "claude-sonnet-4-20250514"
    MAX_TOKENS: int = 4096
    CONFIDENCE_THRESHOLD: float = 0.65

    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
