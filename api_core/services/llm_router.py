"""LLM routing and orchestration logic."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ..config import Settings
from ..rag.retriever import Retriever
from .confidence import ConfidenceEvaluator
from ..adapters.llm_base import ChatMessage, LlmResult, LlmAdapter
from ..adapters.registry import AdapterRegistry


@dataclass
class LlmRouter:
    """Route prompts to the correct LLM provider and enrich with RAG."""

    settings: Settings
    retriever: Retriever
    confidence: ConfidenceEvaluator
    adapters: AdapterRegistry

    def generate_reply(
        self,
        dialog_history: List[ChatMessage],
        system_prompt: str,
    ) -> LlmResult:
        """Retrieve knowledge, call the selected LLM and compute confidence."""

        adapter = self.adapters.get(self.settings.llm_provider)
        knowledge = self.retriever.retrieve(dialog_history[-1].content if dialog_history else "", k=3)
        enriched_messages = dialog_history.copy()
        if knowledge:
            enriched_messages.append(ChatMessage(role="system", content=self._format_context(knowledge)))
        result = adapter.generate(
            messages=enriched_messages,
            system=system_prompt,
            tools=None,
            model=self.settings.llm_model,
            temperature=self.settings.temperature,
            timeout=30,
            extra_ctx={"knowledge": knowledge},
        )
        confidence = self.confidence.score(result.text, result.citations)
        return LlmResult(
            text=result.text,
            confidence=confidence,
            citations=result.citations,
            provider=result.provider,
        )

    def _format_context(self, knowledge: Iterable[dict]) -> str:
        formatted = [f"[{chunk['id']}] {chunk['text']}" for chunk in knowledge]
        return "\n".join(["Relevant knowledge chunks:"] + formatted)
