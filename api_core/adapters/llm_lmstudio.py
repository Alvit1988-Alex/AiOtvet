"""LM Studio adapter built upon OpenAI compatible mock."""
from __future__ import annotations

from typing import Iterable, List

from .llm_base import ChatMessage, LlmAdapter, LlmResult
from .llm_openai import OpenAILlmAdapter


class LmStudioLlmAdapter(LlmAdapter):
    name = "lmstudio"

    def __init__(self) -> None:
        self._delegate = OpenAILlmAdapter()

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
        return self._delegate.generate(messages, system, tools, model, temperature, timeout, extra_ctx)

    def embed(self, texts: Iterable[str], model: str) -> List[List[float]]:
        return self._delegate.embed(texts, model)
