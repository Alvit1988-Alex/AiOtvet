"""Base interfaces for LLM adapters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class LlmResult:
    text: str
    confidence: float
    citations: List[dict]
    provider: str
    payload: Optional[dict] = None


class LlmAdapter:
    """Adapter interface to normalise provider APIs."""

    name: str

    def generate(
        self,
        messages: List[ChatMessage],
        system: str,
        tools: Optional[dict],
        model: str,
        temperature: float,
        timeout: int,
        extra_ctx: dict,
    ) -> LlmResult:
        raise NotImplementedError

    def embed(self, texts: Iterable[str], model: str) -> List[List[float]]:
        raise NotImplementedError
