"""Minimal OpenAI compatible adapter used for tests."""
from __future__ import annotations

import random
from typing import Iterable, List

from .llm_base import ChatMessage, LlmAdapter, LlmResult


class OpenAILlmAdapter(LlmAdapter):
    """Adapter that simulates OpenAI responses for offline testing."""

    name = "openai"

    def __init__(self) -> None:
        random.seed(42)

    def generate(
        self,
        messages: List[ChatMessage],
        system: str,
        tools: dict | None,
        model: str,
        temperature: float,
        timeout: int,
        extra_ctx: dict,
    ) -> LlmResult:
        last = messages[-1].content if messages else ""
        knowledge = extra_ctx.get("knowledge", [])
        citations = [
            {"id": chunk["id"], "text": chunk["text"]}
            for chunk in knowledge
        ]
        reply = f"System:{system[:40]} | Echo:{last}"
        return LlmResult(text=reply, confidence=0.5, citations=citations, provider=self.name)

    def embed(self, texts: Iterable[str], model: str) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for text in texts:
            tokens = text.split()
            if not tokens:
                embeddings.append([0.0])
                continue
            avg = sum(len(token) for token in tokens) / len(tokens)
            embeddings.append([avg, float(len(tokens))])
        return embeddings
