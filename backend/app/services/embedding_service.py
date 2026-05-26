from __future__ import annotations

import hashlib
import math
from typing import Iterable

from app.core.config import settings


class EmbeddingService:
    """OpenAI-compatible embedding facade with deterministic local fallback."""

    dimensions = 384

    def embed_text(self, text: str) -> list[float]:
        if settings.openai_api_key:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=settings.openai_api_key)
                response = client.embeddings.create(model="text-embedding-3-small", input=text[:8000])
                return response.data[0].embedding
            except Exception:
                pass
        return self._local_hash_embedding(text)

    def similarity(self, left: Iterable[float], right: Iterable[float]) -> float:
        lvec = list(left)
        rvec = list(right)
        denom = math.sqrt(sum(x * x for x in lvec)) * math.sqrt(sum(x * x for x in rvec))
        if not denom:
            return 0.0
        return sum(a * b for a, b in zip(lvec, rvec)) / denom

    def _local_hash_embedding(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in (text or "").lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:2], "big") % self.dimensions
            vector[idx] += 1.0 if digest[2] % 2 else -1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [round(value / norm, 6) for value in vector]
