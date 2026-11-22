import asyncio
from app.services.retrieval.vector_store import InMemoryVectorStore
from app.services.retrieval.bm25 import BM25Index
from app.services.retrieval.embeddings import DeterministicLocalEmbeddingProvider
from app.services.retrieval.hybrid import HybridRetrievalService


def test_tenant_isolation_in_retrieval():
    async def _run():
        vs = InMemoryVectorStore()
        bm25 = BM25Index()
        embedder = DeterministicLocalEmbeddingProvider(dimension=64)

        # Tenant A document
        vA = await embedder.embed_texts(["Company secret revenue growth is 25%"])
        await vs.add_vectors(["cA"], vA, [{"tenant_id": "tenant_A", "collection_id": "col_A", "document_id": "doc_A", "text": "Company secret revenue growth is 25%"}])
        bm25.add_documents(["cA"], ["Company secret revenue growth is 25%"], [{"tenant_id": "tenant_A", "collection_id": "col_A", "document_id": "doc_A"}])

        # Tenant B document
        vB = await embedder.embed_texts(["Public open terms and refund policy"])
        await vs.add_vectors(["cB"], vB, [{"tenant_id": "tenant_B", "collection_id": "col_B", "document_id": "doc_B", "text": "Public open terms and refund policy"}])
        bm25.add_documents(["cB"], ["Public open terms and refund policy"], [{"tenant_id": "tenant_B", "collection_id": "col_B", "document_id": "doc_B"}])

        # Query for "revenue growth" as Tenant B - MUST NOT return Tenant A's chunk
        q_vec = (await embedder.embed_texts(["revenue growth"]))[0]
        results_vs = await vs.search(query_vector=q_vec, top_k=5, tenant_id="tenant_B")
        assert all(r.metadata["tenant_id"] == "tenant_B" for r in results_vs)

        results_bm25 = bm25.search(query="revenue growth", top_k=5, tenant_id="tenant_B")
        assert all(r.metadata["tenant_id"] == "tenant_B" for r in results_bm25)

    asyncio.run(_run())
