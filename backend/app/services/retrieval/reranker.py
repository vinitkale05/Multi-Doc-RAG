from abc import ABC, abstractmethod
from typing import List, Tuple
from app.core.config import settings
from app.services.retrieval.hybrid import HybridRetrievedChunk


class ScoredChunk:
    def __init__(self, chunk: HybridRetrievedChunk, rerank_score: float):
        self.chunk = chunk
        self.rerank_score = rerank_score


class BaseReranker(ABC):
    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: List[HybridRetrievedChunk],
        top_n: int = settings.RERANK_TOP_N,
        threshold: float = settings.RERANK_THRESHOLD
    ) -> Tuple[List[ScoredChunk], bool]:
        """Returns (scored_chunks, insufficient_evidence_flag)."""
        pass


COMMON_STOP_WORDS = {
    "what", "is", "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "are", "were", "was", "be", "this", "that", "these", "those",
    "how", "do", "does", "did", "can", "could", "would", "should", "me", "my", "you",
    "it", "its", "their", "there", "has", "have", "had", "been", "will"
}

QUERY_INTENT_WORDS = {
    "give", "tell", "show", "list", "summarize", "summary", "explain", "describe",
    "imp", "important", "main", "key", "points", "point", "detail", "details",
    "highlight", "highlights", "overview", "all", "everything", "provide",
    "resume", "document", "file", "text", "paper", "data", "information"
}


class SimpleHeuristicReranker(BaseReranker):
    """Fast, accurate cross-scoring combining semantic rank, term overlap, and exact phrase match."""

    async def rerank(
        self,
        query: str,
        candidates: List[HybridRetrievedChunk],
        top_n: int = settings.RERANK_TOP_N,
        threshold: float = settings.RERANK_THRESHOLD
    ) -> Tuple[List[ScoredChunk], bool]:
        if not candidates:
            return [], True

        import re
        q_raw = [w.lower() for w in re.findall(r"\w+", query)]
        # Content keywords (excluding intent/command words)
        content_terms = {w for w in q_raw if w not in COMMON_STOP_WORDS and w not in QUERY_INTENT_WORDS and len(w) > 2}
        all_query_terms = {w for w in q_raw if w not in COMMON_STOP_WORDS and len(w) > 2}

        scored: List[ScoredChunk] = []

        for candidate in candidates:
            text = candidate.text.lower()
            # 1. Exact phrase boost
            exact_boost = 0.35 if query.lower() in text else 0.0

            # 2. Term overlap ratio
            terms_to_check = content_terms if content_terms else all_query_terms
            if terms_to_check:
                matched_terms = sum(1 for t in terms_to_check if t in text)
                overlap_ratio = matched_terms / len(terms_to_check)
            else:
                overlap_ratio = 1.0

            # 3. Base RRF score normalized (dense vector similarity + BM25)
            norm_rrf = min(1.0, candidate.rrf_score * 30.0)

            # Composite score blends semantic rank (RRF) and lexical overlap
            composite_score = 0.50 * norm_rrf + 0.35 * overlap_ratio + 0.15 * exact_boost
            
            # Keep chunk if it has reasonable relevance
            if composite_score >= 0.08 or norm_rrf >= 0.10 or overlap_ratio >= 0.20:
                scored.append(ScoredChunk(chunk=candidate, rerank_score=composite_score))

        # Fallback: if candidates were retrieved but heuristic scoring was too strict, retain top candidates
        if not scored and candidates:
            for candidate in candidates[:top_n]:
                scored.append(ScoredChunk(chunk=candidate, rerank_score=0.25))

        scored.sort(key=lambda x: x.rerank_score, reverse=True)
        top_scored = scored[:top_n]

        insufficient_evidence = len(top_scored) == 0
        return top_scored, insufficient_evidence


def get_reranker() -> BaseReranker:
    return SimpleHeuristicReranker()
