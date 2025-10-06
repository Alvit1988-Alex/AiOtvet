"""Registry for LLM adapters."""
from __future__ import annotations

from typing import Dict

from .llm_base import LlmAdapter


class AdapterRegistry:
    """Simple adapter registry that supports runtime switching."""

    def __init__(self) -> None:
        self._registry: Dict[str, LlmAdapter] = {}

    def register(self, name: str, adapter: LlmAdapter) -> None:
        self._registry[name] = adapter

    def get(self, name: str) -> LlmAdapter:
        try:
            return self._registry[name]
        except KeyError as exc:
            raise KeyError(f"LLM provider '{name}' not registered") from exc

    def all(self) -> Dict[str, LlmAdapter]:
        return dict(self._registry)
