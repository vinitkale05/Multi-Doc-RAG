from typing import List, Dict, Any, Optional
from collections import defaultdict
from app.services.retrieval.vector_store import get_vector_store, VectorSearchResult
from app.services.retrieval.bm25 import get_bm25_index, BM25SearchResult
from app.services.retrieval.embeddings import get_embedding_provider


class HybridRetrievedChunk:
    def __init__(self, chunk_id: str, rrf_score: float, text: str, metadata: Dict[str, Any]):
        self.chunk_id = chunk_id
        self.rrf_score = rrf_score
        self.text = text
        self.metadata = metadata


class HybridRetrievalService:
    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k
        self.vector_store = get_vector_store()
        self.bm25_index = get_bm25_index()
        self.embedding_provider = get_embedding_provider()

    async def retrieve(
        self,
        query: str,
        tenant_id: str,
        collection_ids: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None,
        top_k: int = 30
    ) -> List[HybridRetrievedChunk]:
        # 1. Dense vector search
        query_vectors = await self.embedding_provider.embed_texts([query])
        query_vector = query_vectors[0]
        dense_results = await self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            tenant_id=tenant_id,
            collection_ids=collection_ids,
            document_ids=document_ids
        )

        # 2. Sparse BM25 search
        bm25_results = self.bm25_index.search(
            query=query,
            top_k=top_k,
            tenant_id=tenant_id,
            collection_ids=collection_ids,
            document_ids=document_ids
        )

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = defaultdict(float)
        chunk_metadatas: Dict[str, Dict[str, Any]] = {}

        # Dense ranks
        for rank, res in enumerate(dense_results):
            rrf_scores[res.chunk_id] += 1.0 / (self.rrf_k + (rank + 1))
            chunk_metadatas[res.chunk_id] = res.metadata

        # BM25 ranks
        for rank, res in enumerate(bm25_results):
            rrf_scores[res.chunk_id] += 1.0 / (self.rrf_k + (rank + 1))
            chunk_metadatas[res.chunk_id] = res.metadata

        # 4. Multi-document coverage balancing
        # Group by document to prevent single document from starving others in comparative queries
        doc_count = defaultdict(int)
        balanced_results = []

        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        for cid in sorted_cids:
            meta = chunk_metadatas[cid]
            doc_id = meta.get("document_id")
            # Apply slight diversity penalty if a document already has >= 3 chunks in top-k
            penalty = 1.0 / (1.0 + 0.15 * doc_count[doc_id])
            final_score = rrf_scores[cid] * penalty
            doc_count[doc_id] += 1

            balanced_results.append(
                HybridRetrievedChunk(
                    chunk_id=cid,
                    rrf_score=final_score,
                    text=meta.get("text", ""),
                    metadata=meta
                )
            )

        balanced_results.sort(key=lambda x: x.rrf_score, reverse=True)
        return balanced_results[:top_k]
