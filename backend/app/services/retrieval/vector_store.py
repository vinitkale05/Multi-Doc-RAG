import os
import pickle
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
from app.core.config import settings

PERSIST_PATH = os.path.join(settings.LOCAL_STORAGE_DIR, "vector_store.pkl")


class VectorSearchResult:
    def __init__(self, chunk_id: str, score: float, metadata: Dict[str, Any]):
        self.chunk_id = chunk_id
        self.score = score
        self.metadata = metadata


class BaseVectorStore(ABC):
    @abstractmethod
    async def add_vectors(
        self,
        chunk_ids: List[str],
        vectors: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        top_k: int,
        tenant_id: str,
        collection_ids: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[VectorSearchResult]:
        pass

    @abstractmethod
    async def delete_by_document(self, document_id: str) -> None:
        pass

    @abstractmethod
    async def delete_by_collection(self, collection_id: str) -> None:
        pass


class InMemoryVectorStore(BaseVectorStore):
    def __init__(self):
        # chunk_id -> {"vector": np.array, "metadata": dict}
        self._store: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        try:
            if os.path.exists(PERSIST_PATH):
                with open(PERSIST_PATH, "rb") as f:
                    self._store = pickle.load(f)
        except Exception:
            self._store = {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(PERSIST_PATH), exist_ok=True)
            with open(PERSIST_PATH, "wb") as f:
                pickle.dump(self._store, f)
        except Exception:
            pass

    async def add_vectors(
        self,
        chunk_ids: List[str],
        vectors: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        for cid, vec, meta in zip(chunk_ids, vectors, metadatas):
            v_arr = np.array(vec, dtype=np.float32)
            norm = np.linalg.norm(v_arr)
            if norm > 0:
                v_arr = v_arr / norm
            self._store[cid] = {"vector": v_arr, "metadata": meta}
        self._save()

    async def search(
        self,
        query_vector: List[float],
        top_k: int,
        tenant_id: str,
        collection_ids: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[VectorSearchResult]:
        q_arr = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_arr)
        if q_norm > 0:
            q_arr = q_arr / q_norm

        results = []
        for cid, item in self._store.items():
            meta = item["metadata"]
            # Strict tenant boundary check
            if meta.get("tenant_id") != tenant_id:
                continue

            # Collection filter
            if collection_ids and meta.get("collection_id") not in collection_ids:
                continue

            # Document filter
            if document_ids and meta.get("document_id") not in document_ids:
                continue

            # Cosine similarity
            score = float(np.dot(q_arr, item["vector"]))
            results.append(VectorSearchResult(chunk_id=cid, score=score, metadata=meta))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    async def delete_by_document(self, document_id: str) -> None:
        to_del = [cid for cid, item in self._store.items() if item["metadata"].get("document_id") == document_id]
        for cid in to_del:
            del self._store[cid]
        self._save()

    async def delete_by_collection(self, collection_id: str) -> None:
        to_del = [cid for cid, item in self._store.items() if item["metadata"].get("collection_id") == collection_id]
        for cid in to_del:
            del self._store[cid]
        self._save()


# Global singleton instance
vector_store_instance = InMemoryVectorStore()


def get_vector_store() -> BaseVectorStore:
    return vector_store_instance
