import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = "development"
    APP_NAME: str = "Multi-Document RAG with Citations"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'rag_database.db'))}"

    # Vector store
    VECTOR_STORE: str = "inmemory"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_DIR: str = "./storage_data"
    OBJECT_STORE_ENDPOINT: str = "http://localhost:9000"
    OBJECT_STORE_BUCKET: str = "rag-docs"
    OBJECT_STORE_ACCESS_KEY: str = "minioadmin"
    OBJECT_STORE_SECRET_KEY: str = "minioadmin"

    # LLM & Generation
    LLM_PROVIDER: str = "mock"  # openai | gemini | ollama | mock
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1500

    # Embedding
    EMBEDDING_PROVIDER: str = "mock"  # openai | gemini | local | mock
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_API_KEY: str = ""

    # Reranking
    RERANKER_PROVIDER: str = "simple"  # cross-encoder | simple | mock
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_THRESHOLD: float = 0.25
    RERANK_TOP_N: int = 8
    RETRIEVAL_TOP_K: int = 30

    # Chunking
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP: int = 100

    # Auth & Security
    JWT_SECRET: str = "production_ready_super_secret_key_change_me_in_prod_1234567890"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TTL_MINUTES: int = 15
    JWT_REFRESH_TTL_DAYS: int = 7
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]

    # Limits & Quotas
    RATE_LIMIT_PER_MIN: int = 60
    MAX_UPLOAD_MB: int = 50
    MAX_PAGES: int = 500
    TOKEN_BUDGET_DAILY: int = 100000

    # Observability
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""


settings = Settings()
