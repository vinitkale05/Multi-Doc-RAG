import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import init_db
from app.core.errors import AppError
from app.api.v1.auth import router as auth_router
from app.api.v1.collections import router as collections_router
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.citations import router as citations_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.admin import router as admin_router
from app.api.v1.health import router as health_router
from app.api.v1.notebook import router as notebook_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("multi_doc_rag")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Multi-Document RAG with Citations platform...")
    await init_db()
    logger.info("Database schema synchronized.")
    try:
        await sync_knowledge_base()
    except Exception as e:
        logger.warning(f"Knowledge base sync warning: {e}")
    yield
    logger.info("Shutting down Multi-Document RAG platform.")


async def sync_knowledge_base():
    from app.core.database import AsyncSessionLocal
    from app.models import Chunk, Document, Collection
    from app.services.retrieval.vector_store import get_vector_store
    from app.services.retrieval.bm25 import get_bm25_index
    from app.services.retrieval.embeddings import get_embedding_provider
    from sqlalchemy import select

    vs = get_vector_store()
    bm = get_bm25_index()
    emb = get_embedding_provider()

    async with AsyncSessionLocal() as db:
        stmt = (
            select(Chunk, Document.collection_id, Document.filename, Collection.tenant_id)
            .join(Document, Chunk.document_id == Document.id)
            .join(Collection, Document.collection_id == Collection.id)
            .where(Document.status == "READY")
        )
        res = await db.execute(stmt)
        rows = res.all()

        missing_cids = []
        missing_texts = []
        missing_metas = []

        for chunk, collection_id, filename, tenant_id in rows:
            if chunk.id not in vs._store or chunk.id not in bm.docs:
                meta = {
                    "document_id": chunk.document_id,
                    "collection_id": collection_id,
                    "tenant_id": tenant_id,
                    "filename": filename,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "section_path": chunk.section_path,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end,
                    "text": chunk.text,
                }
                missing_cids.append(chunk.id)
                missing_texts.append(chunk.text)
                missing_metas.append(meta)

        if missing_cids:
            logger.info(f"Syncing {len(missing_cids)} chunks to vector store and BM25 index...")
            vectors = await emb.embed_texts(missing_texts)
            await vs.add_vectors(missing_cids, vectors, missing_metas)
            bm.add_documents(missing_cids, missing_texts, missing_metas)
            logger.info("Knowledge base synchronization complete.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade Multi-Document RAG platform with verifiable inline citations, hybrid retrieval, and prompt injection defense.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local and container setups
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Custom Exception Handler
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

# Include Routers under /api/v1
api_v1 = FastAPI()
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(collections_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(citations_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(notebook_router, prefix="/api/v1")

# Root redirect or health
@app.get("/")
async def root():
    return {
        "product": settings.APP_NAME,
        "author": "Vinit Kale",
        "status": "online",
        "documentation": "/docs",
        "api_prefix": "/api/v1"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
