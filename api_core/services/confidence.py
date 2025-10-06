"""Confidence scoring heuristics."""
from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Iterable


@dataclass
class ConfidenceEvaluator:
    """Simple heuristic evaluating LLM confidence."""

    threshold: float

    def score(self, text: str, citations: Iterable[dict] | None = None) -> float:
        """Return a pseudo confidence based on length and citations."""

        length_score = 1 - exp(-len(text) / 100)
        citation_bonus = 0.1 if citations else 0.0
        confidence = min(1.0, max(0.0, length_score + citation_bonus))
        return confidence
