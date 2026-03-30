"""RAG pipeline orchestrating the 7-step reasoning flow.

Steps:
1. Intake — receive and validate the question
2. Intent classification — determine query type via Claude
3. Graph traversal — execute the appropriate Cypher query
4. Context serialization — convert results to LLM-friendly format
5. LLM generation — call Claude with graph context
6. Confidence scoring — evaluate response quality
7. Response delivery — return or stream the result
"""

from __future__ import annotations

import logging
import re
from collections.abc import AsyncGenerator
from typing import Any

import anthropic

from crip_shared.graph import GraphDB

from app.rag.confidence import score_confidence
from app.rag.context import serialize_graph_context
from app.rag.graph_queries import (
    attack_path_query,
    coverage_gap_query,
    general_query,
    remediation_query,
)
from app.rag.intent import classify_intent
from app.llm.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Orchestrates intent classification, graph retrieval, and LLM generation.

    Supports both synchronous (full response) and streaming (token-by-token) modes.
    """

    def __init__(
        self,
        graph: GraphDB,
        llm_client: anthropic.Anthropic,
        model: str,
        max_tokens: int = 4096,
    ) -> None:
        self._graph = graph
        self._llm = llm_client
        self._model = model
        self._max_tokens = max_tokens

    async def _classify(self, question: str) -> dict:
        """Step 2: Intent classification."""
        return await classify_intent(question, self._llm, self._model)

    async def _retrieve(self, intent_result: dict, tenant_id: str) -> list[dict]:
        """Step 3: Graph traversal based on classified intent."""
        intent = intent_result["intent"]

        if intent == "attack_path":
            cypher, params = attack_path_query(
                tenant_id, intent_result.get("actor"), intent_result.get("target_type")
            )
        elif intent == "coverage_gap":
            cypher, params = coverage_gap_query(tenant_id)
        elif intent == "remediation":
            cypher, params = remediation_query(tenant_id)
        elif intent == "apt_simulation":
            # APT simulation uses attack path queries scoped to the actor
            cypher, params = attack_path_query(
                tenant_id, intent_result.get("actor"), None
            )
        else:
            # Extract keywords from the question for general search
            keywords = [
                w for w in intent_result.get("actor", "").split()
                if len(w) > 2
            ] if intent_result.get("actor") else None
            cypher, params = general_query(tenant_id, keywords)

        return await self._graph.query(cypher, params)

    def _build_user_message(self, question: str, context: str) -> str:
        """Build the user message with graph context and question."""
        return (
            f"## Graph Context\n{context}\n\n"
            f"## Analyst Question\n{question}"
        )

    async def run_sync(
        self,
        question: str,
        tenant_id: str,
        session_id: str,
    ) -> dict[str, Any]:
        """Execute the full pipeline and return the complete result.

        Returns:
            Dict with keys: answer, confidence, citations, intent.
        """
        # Step 2: Intent classification
        intent_result = await self._classify(question)
        logger.info("Intent: %s (confidence=%.2f)", intent_result["intent"], intent_result["confidence"])

        # Step 3: Graph traversal
        graph_results = await self._retrieve(intent_result, tenant_id)
        logger.info("Graph returned %d rows", len(graph_results))

        # Step 4: Context serialization
        context = serialize_graph_context(graph_results)

        # Step 5: LLM generation
        user_message = self._build_user_message(question, context)
        response = self._llm.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        answer = response.content[0].text

        # Step 6: Confidence scoring
        confidence = score_confidence(graph_results, answer, intent_result["intent"])

        # Step 7: Extract citations
        citations = re.findall(r"\[NODE:\d+\]", answer)

        return {
            "answer": answer,
            "confidence": confidence,
            "citations": citations,
            "intent": intent_result["intent"],
        }

    async def run_streaming(
        self,
        question: str,
        tenant_id: str,
        session_id: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute the pipeline with streaming LLM output.

        Yields:
            Dicts with type "token" (content=str) or "done" (confidence, citations).
        """
        # Steps 2-4 are the same as sync
        intent_result = await self._classify(question)
        graph_results = await self._retrieve(intent_result, tenant_id)
        context = serialize_graph_context(graph_results)
        user_message = self._build_user_message(question, context)

        # Step 5: Streaming LLM generation
        full_response = ""
        with self._llm.messages.stream(
            model=self._model,
            max_tokens=self._max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                yield {"type": "token", "content": text}

        # Step 6: Confidence scoring
        confidence = score_confidence(graph_results, full_response, intent_result["intent"])

        # Step 7: Extract citations and signal completion
        citations = re.findall(r"\[NODE:\d+\]", full_response)
        yield {
            "type": "done",
            "confidence": confidence,
            "citations": citations,
        }
