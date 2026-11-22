from abc import ABC, abstractmethod
from typing import List
import hashlib
import math
import numpy as np
import httpx
from app.core.config import settings


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        pass


class DeterministicLocalEmbeddingProvider(BaseEmbeddingProvider):
    """Zero-dependency deterministic 384-dimensional semantic projection.

    Uses bag-of-words & character n-gram hashing with unit-norm projection.
    Provides fast, reproducible, and zero-cost dense embeddings for testing and local dev.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _embed_single(self, text: str) -> List[float]:
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec.tolist()

        for word in words:
            # Word level hash
            h_val = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h_val % self.dimension
            sign = 1.0 if (h_val >> 1) % 2 == 0 else -1.0
            vec[idx] += sign

            # 3-gram character hashes for sub-word semantics
            for i in range(len(word) - 2):
                ngram = word[i : i + 3]
                nh = int(hashlib.sha256(ngram.encode("utf-8")).hexdigest(), 16)
                nidx = nh % self.dimension
                nsign = 1.0 if (nh >> 1) % 2 == 0 else -1.0
                vec[nidx] += 0.5 * nsign

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_single(t) for t in texts]

    def get_dimension(self) -> int:
        return self.dimension


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str = settings.EMBEDDING_API_KEY, model: str = settings.EMBEDDING_MODEL):
        self.api_key = api_key
        self.model = model
        self.dimension = settings.EMBEDDING_DIMENSION

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            fallback = DeterministicLocalEmbeddingProvider(self.dimension)
            return await fallback.embed_texts(texts)

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"input": texts, "model": self.model},
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            return [item["embedding"] for item in data]

    def get_dimension(self) -> int:
        return self.dimension


def get_embedding_provider() -> BaseEmbeddingProvider:
    if settings.EMBEDDING_PROVIDER == "openai" and settings.EMBEDDING_API_KEY:
        return OpenAIEmbeddingProvider()
    return DeterministicLocalEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)
