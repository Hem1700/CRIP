"""Intent classification for analyst questions using Claude."""

from __future__ import annotations

import json
import logging

import anthropic

logger = logging.getLogger(__name__)

INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for a cyber risk intelligence platform.
Classify the user question into exactly one of these intents:

- attack_path: Questions about how a threat actor could reach a target asset, lateral movement, kill chains.
- coverage_gap: Questions about missing security controls, EDR gaps, unpatched systems, blind spots.
- remediation: Questions about what to fix first, patch priorities, risk reduction recommendations.
- apt_simulation: Questions about specific APT groups, their TTPs, or simulating their behavior.
- general: Anything else — asset lookups, counts, status checks, broad questions.

Also extract:
- actor: The threat actor name if mentioned (or null).
- target_type: The type of target asset if mentioned (or null).

Respond ONLY with a JSON object, no other text:
{"intent": "...", "actor": "..." or null, "target_type": "..." or null, "confidence": 0.0-1.0}"""


async def classify_intent(
    question: str,
    llm_client: anthropic.Anthropic,
    model: str = "claude-sonnet-4-20250514",
) -> dict:
    """Classify a user question into a known intent using Claude.

    Args:
        question: The analyst's natural language question.
        llm_client: Anthropic client instance.
        model: Model to use for classification.

    Returns:
        Dict with keys: intent, actor, target_type, confidence.
    """
    try:
        response = llm_client.messages.create(
            model=model,
            max_tokens=256,
            system=INTENT_CLASSIFICATION_PROMPT,
            messages=[{"role": "user", "content": question}],
        )

        text = response.content[0].text.strip()
        result = json.loads(text)

        # Validate required fields
        valid_intents = {"attack_path", "coverage_gap", "remediation", "apt_simulation", "general"}
        if result.get("intent") not in valid_intents:
            result["intent"] = "general"
            result["confidence"] = 0.5

        return {
            "intent": result["intent"],
            "actor": result.get("actor"),
            "target_type": result.get("target_type"),
            "confidence": float(result.get("confidence", 0.7)),
        }

    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.warning("Intent classification failed, defaulting to general: %s", exc)
        return {
            "intent": "general",
            "actor": None,
            "target_type": None,
            "confidence": 0.5,
        }
