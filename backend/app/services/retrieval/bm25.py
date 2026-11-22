import os
import math
import re
import pickle
from typing import List, Dict, Any, Optional
from collections import Counter
from app.core.config import settings

BM25_PERSIST_PATH = os.path.join(settings.LOCAL_STORAGE_DIR, "bm25_index.pkl")


class BM25SearchResult:
    def __init__(self, chunk_id: str, score: float, metadata: Dict[str, Any]):
        self.chunk_id = chunk_id
        self.score = score
        self.metadata = metadata


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        # chunk_id -> {"tokens": List[str], "metadata": dict, "len": int}
        self.docs: Dict[str, Dict[str, Any]] = {}
        # token -> set of chunk_ids
        self.inverted_index: Dict[str, set] = {}
        self.total_tokens: int = 0
        self._load()

    def _load(self):
        try:
            if os.path.exists(BM25_PERSIST_PATH):
                with open(BM25_PERSIST_PATH, "rb") as f:
                    data = pickle.load(f)
                    self.docs = data.get("docs", {})
                    self.inverted_index = data.get("inverted_index", {})
                    self.total_tokens = data.get("total_tokens", 0)
        except Exception:
            pass

    def _save(self):
        try:
            os.makedirs(os.path.dirname(BM25_PERSIST_PATH), exist_ok=True)
            with open(BM25_PERSIST_PATH, "wb") as f:
                pickle.dump({
                    "docs": self.docs,
                    "inverted_index": self.inverted_index,
                    "total_tokens": self.total_tokens
                }, f)
        except Exception:
            pass

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\w+", text) if len(w) > 1]

    def add_documents(self, chunk_ids: List[str], texts: List[str], metadatas: List[Dict[str, Any]]):
        for cid, text, meta in zip(chunk_ids, texts, metadatas):
            tokens = self._tokenize(text)
            self.docs[cid] = {
                "tokens": tokens,
                "counts": Counter(tokens),
                "metadata": meta,
                "len": len(tokens)
            }
            self.total_tokens += len(tokens)
            for t in set(tokens):
                if t not in self.inverted_index:
                    self.inverted_index[t] = set()
                self.inverted_index[t].add(cid)
        self._save()

    def search(
        self,
        query: str,
        top_k: int,
        tenant_id: str,
        collection_ids: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[BM25SearchResult]:
        q_tokens = self._tokenize(query)
        if not q_tokens or not self.docs:
            return []

        N = len(self.docs)
        avgdl = self.total_tokens / max(1, N)

        scores: Dict[str, float] = {}

        # Candidate chunks containing at least one query token
        matching_chunk_ids = set()
        for t in q_tokens:
            if t in self.inverted_index:
                matching_chunk_ids.update(self.inverted_index[t])

        for cid in matching_chunk_ids:
            doc_info = self.docs[cid]
            meta = doc_info["metadata"]

            # Filter tenant
            if meta.get("tenant_id") != tenant_id:
                continue
            # Filter collection
            if collection_ids and meta.get("collection_id") not in collection_ids:
                continue
            # Filter document
            if document_ids and meta.get("document_id") not in document_ids:
                continue

            doc_len = doc_info["len"]
            counts = doc_info["counts"]
            score = 0.0

            for t in q_tokens:
                if t in counts:
                    tf = counts[t]
                    df = len(self.inverted_index.get(t, []))
                    # IDF with Robertson-Spärck Jones formula
                    idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / avgdl))
                    score += idf * (tf * (self.k1 + 1.0)) / denom

            if score > 0:
                scores[cid] = score

        results = [
            BM25SearchResult(chunk_id=cid, score=score, metadata=self.docs[cid]["metadata"])
            for cid, score in scores.items()
        ]
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def delete_by_document(self, document_id: str):
        to_del = [cid for cid, info in self.docs.items() if info["metadata"].get("document_id") == document_id]
        for cid in to_del:
            self.total_tokens -= self.docs[cid]["len"]
            del self.docs[cid]
        # Rebuild inverted index cleanly
        self.inverted_index = {}
        for cid, info in self.docs.items():
            for t in set(info["tokens"]):
                if t not in self.inverted_index:
                    self.inverted_index[t] = set()
                self.inverted_index[t].add(cid)
        self._save()

    def delete_by_collection(self, collection_id: str):
        to_del = [cid for cid, info in self.docs.items() if info["metadata"].get("collection_id") == collection_id]
        for cid in to_del:
            self.total_tokens -= self.docs[cid]["len"]
            del self.docs[cid]
        self.inverted_index = {}
        for cid, info in self.docs.items():
            for t in set(info["tokens"]):
                if t not in self.inverted_index:
                    self.inverted_index[t] = set()
                self.inverted_index[t].add(cid)
        self._save()


bm25_instance = BM25Index()


def get_bm25_index() -> BM25Index:
    return bm25_instance
