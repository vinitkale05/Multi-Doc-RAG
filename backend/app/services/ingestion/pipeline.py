import hashlib
import logging
from typing import BinaryIO, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models import Document, Chunk, Collection
from app.services.storage.storage import get_storage_service
from app.services.ingestion.parsers import get_parser
from app.services.ingestion.cleaner import sanitize_document_text
from app.services.ingestion.chunker import StructureAwareChunker
from app.services.retrieval.embeddings import get_embedding_provider
from app.services.retrieval.vector_store import get_vector_store
from app.services.retrieval.bm25 import get_bm25_index
from app.core.events import event_bus

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(self):
        self.storage_service = get_storage_service()
        self.embedding_provider = get_embedding_provider()
        self.vector_store = get_vector_store()
        self.bm25_index = get_bm25_index()

    async def ingest_document(
        self,
        db: AsyncSession,
        document_id: str,
        content_bytes: bytes,
        filename: str,
        mime_type: str,
        tenant_id: str
    ) -> Document:
        """Executes full asynchronous ingestion lifecycle for a document."""
        # 1. Fetch document record
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalars().first()
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        try:
            # Event: QUEUED -> PARSING
            doc.status = "PARSING"
            await db.commit()
            await event_bus.publish(document_id, {"status": "PARSING", "progress": 0.2, "message": "Parsing document layout and text"})

            parser = get_parser(filename, mime_type)
            parsed_pages = parser.parse(content_bytes, filename)
            doc.page_count = len(parsed_pages)

            # Sanitize each page
            for p in parsed_pages:
                cleaned_text, injection_flag = sanitize_document_text(p.text)
                p.text = cleaned_text

            # Event: PARSING -> CHUNKING
            doc.status = "CHUNKING"
            await db.commit()
            await event_bus.publish(document_id, {"status": "CHUNKING", "progress": 0.5, "message": "Extracting structure-aware chunks"})

            # Fetch collection chunk config
            col_res = await db.execute(select(Collection).where(Collection.id == doc.collection_id))
            collection = col_res.scalars().first()
            cfg = collection.chunk_config or {} if collection else {}
            chunk_size = cfg.get("chunk_size", 700)
            chunk_overlap = cfg.get("chunk_overlap", 100)

            chunker = StructureAwareChunker(target_tokens=chunk_size, overlap_tokens=chunk_overlap)
            chunk_items = chunker.chunk_pages(parsed_pages, document_id=doc.id)

            if not chunk_items:
                # Document might be empty text or images
                doc.status = "READY"
                await db.commit()
                await event_bus.publish(document_id, {"status": "READY", "progress": 1.0, "message": "Document ingested (empty content)"})
                return doc

            # Event: CHUNKING -> EMBEDDING
            doc.status = "EMBEDDING"
            await db.commit()
            await event_bus.publish(document_id, {"status": "EMBEDDING", "progress": 0.7, "message": f"Embedding {len(chunk_items)} chunks"})

            chunk_texts = [ci.text for ci in chunk_items]
            chunk_ids = [ci.chunk_id for ci in chunk_items]

            # Generate embeddings
            vectors = await self.embedding_provider.embed_texts(chunk_texts)

            # Prepare metadata for vector store and BM25
            metadatas = []
            for ci in chunk_items:
                meta = {
                    "document_id": doc.id,
                    "collection_id": doc.collection_id,
                    "tenant_id": tenant_id,
                    "filename": filename,
                    "page_start": ci.page_start,
                    "page_end": ci.page_end,
                    "section_path": ci.section_path,
                    "char_start": ci.char_start,
                    "char_end": ci.char_end,
                    "text": ci.text,
                }
                metadatas.append(meta)

            # Write to Vector Store & BM25 Index
            await self.vector_store.add_vectors(chunk_ids, vectors, metadatas)
            self.bm25_index.add_documents(chunk_ids, chunk_texts, metadatas)

            # Insert Chunks to Database
            for ci in chunk_items:
                db_chunk = Chunk(
                    id=ci.chunk_id,
                    document_id=doc.id,
                    ordinal=ci.ordinal,
                    text=ci.text,
                    page_start=ci.page_start,
                    page_end=ci.page_end,
                    section_path=ci.section_path,
                    char_start=ci.char_start,
                    char_end=ci.char_end,
                    token_count=ci.token_count,
                    embedding_model=self.embedding_provider.__class__.__name__
                )
                db.add(db_chunk)

            # Event: READY
            doc.status = "READY"
            doc.error = None
            await db.commit()
            await event_bus.publish(document_id, {"status": "READY", "progress": 1.0, "message": "Document indexed and ready for retrieval"})

            return doc

        except Exception as e:
            logger.exception(f"Ingestion failed for document {document_id}: {e}")
            doc.status = "FAILED"
            doc.error = str(e)
            await db.commit()
            await event_bus.publish(document_id, {"status": "FAILED", "progress": 0.0, "error": str(e), "message": f"Ingestion failed: {str(e)}"})
            raise


ingestion_pipeline = IngestionPipeline()
