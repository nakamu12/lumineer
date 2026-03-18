"""CrossEncoderReranker: neural re-ranking via sentence-transformers."""

from __future__ import annotations

import logging
from typing import Any

from app.infrastructure.reranking.base import BaseReranker

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker(BaseReranker):
    """Reranks using a CrossEncoder model (sentence-transformers).

    Requires: pip install sentence-transformers
    Adds ~200-500ms latency on CPU for top-20 candidates.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        try:
            from sentence_transformers import CrossEncoder

            self._model: Any = CrossEncoder(model_name)
            logger.info("CrossEncoderReranker loaded model: %s", model_name)
        except ImportError as e:
            raise ImportError(
                "sentence-transformers is required for CrossEncoderReranker. "
                "Install it with: pip install sentence-transformers"
            ) from e

    def rerank(
        self,
        query: str,
        results: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        if not results:
            return []

        passages = [r.get("title", "") + " " + r.get("description", "") for r in results]
        pairs = [(query, p) for p in passages]
        raw_scores: list[float] = self._model.predict(pairs).tolist()

        ranked = sorted(
            zip(raw_scores, results),
            key=lambda x: x[0],
            reverse=True,
        )
        return [r for _, r in ranked[:top_k]]
