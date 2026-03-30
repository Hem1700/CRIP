"""LLM client factory — supports direct Anthropic API and AWS Bedrock."""

from __future__ import annotations

import anthropic

from app.config import Settings


def get_llm_client(config: Settings) -> anthropic.Anthropic:
    """Return an Anthropic client configured for direct API or Bedrock.

    Args:
        config: Service settings containing API keys and Bedrock config.

    Returns:
        An anthropic.Anthropic client instance. When USE_BEDROCK is True,
        the client is configured to route through AWS Bedrock.
    """
    if config.USE_BEDROCK:
        return anthropic.AnthropicBedrock(
            aws_region=config.BEDROCK_REGION,
        )

    return anthropic.Anthropic(
        api_key=config.ANTHROPIC_API_KEY,
    )
