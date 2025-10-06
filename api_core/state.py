"""Application wide singletons."""
from __future__ import annotations

from functools import lru_cache

from .adapters import build_default_registry
from .services.confidence import ConfidenceEvaluator
from .services.notifications import NotificationManager


_notifier = NotificationManager()
_adapter_registry = build_default_registry()


def get_notifier() -> NotificationManager:
    return _notifier


def get_adapter_registry():
    return _adapter_registry


def build_confidence(threshold: float) -> ConfidenceEvaluator:
    return ConfidenceEvaluator(threshold=threshold)
