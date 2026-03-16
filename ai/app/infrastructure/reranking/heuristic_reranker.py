"""HeuristicReranker: weighted score combining relevance, rating, and enrolled."""

import math
from typing import Any

from app.infrastructure.reranking.base import BaseReranker

# Weights for the composite score
ALPHA = 0.6  # relevance (RRF score, normalized)
BETA = 0.3  # rating (0-5 → normalized to 0-1)
GAMMA = 0.1  # enrolled (log-normalized)

MAX_RATING = 5.0
LOG_ENROLLED_SCALE = 14.0  # ln(1_200_000) ≈ 14 (rough upper bound)


class HeuristicReranker(BaseReranker):
    """Reranks by: α × relevance + β × (rating/5) + γ × ln(enrolled+1)/scale."""

    def rerank(
        self,
        query: str,
        results: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        if not results:
            return []

        scores = [float(r.get("_score", 0.0)) for r in results]
        max_score = max(scores)
        min_score = min(scores)
        score_range = max_score - min_score or 1.0

        def composite(r: dict[str, Any]) -> float:
            relevance = (float(r.get("_score", 0.0)) - min_score) / score_range
            rating = min(float(r.get("rating", 0.0)), MAX_RATING) / MAX_RATING
            enrolled = math.log1p(float(r.get("enrolled", 0))) / LOG_ENROLLED_SCALE
            return ALPHA * relevance + BETA * rating + GAMMA * enrolled

        ranked = sorted(results, key=composite, reverse=True)
        return ranked[:top_k]
