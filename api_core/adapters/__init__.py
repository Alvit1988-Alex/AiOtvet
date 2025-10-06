"""Register adapters on import."""
from .llm_openai import OpenAILlmAdapter
from .llm_azure import AzureLlmAdapter
from .llm_openrouter import OpenRouterLlmAdapter
from .llm_lmstudio import LmStudioLlmAdapter
from .registry import AdapterRegistry


def build_default_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    registry.register("openai", OpenAILlmAdapter())
    registry.register("azure", AzureLlmAdapter())
    registry.register("openrouter", OpenRouterLlmAdapter())
    registry.register("lmstudio", LmStudioLlmAdapter())
    return registry


__all__ = ["build_default_registry"]
