import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core Application Settings
    APP_NAME: str = "AI Learning Assistant & Mock Interview Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]

    # Database Configuration (SQLAlchemy / PostgreSQL / SQLite)
    DATABASE_URL: str = Field(
        default="sqlite:///./abhyas_ai.db",
        description="SQLAlchemy database connection URL (PostgreSQL or SQLite)",
    )


    # AWS Credentials & Bedrock Configuration
    AWS_REGION: str = Field(default="us-east-1", description="AWS Region")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, description="AWS Access Key ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, description="AWS Secret Access Key")
    AWS_SESSION_TOKEN: Optional[str] = Field(
        default=None, description="AWS Session Token for temporary credentials"
    )
    BEDROCK_MODEL_ID: str = Field(
        default="anthropic.claude-3-haiku-20240307-v1:0",
        description="AWS Bedrock LLM Model ID",
    )
    AWS_S3_BUCKET_NAME: Optional[str] = Field(
        default=None, description="AWS S3 Bucket Name for media and document assets"
    )

    # Vector DB API Keys & Configuration
    VECTOR_DB_TYPE: str = Field(
        default="chroma",
        description="Vector DB provider (e.g. chroma, pinecone, qdrant, weaviate)",
    )
    VECTOR_DB_API_KEY: Optional[str] = Field(
        default=None, description="API Key for managed Vector DB services"
    )
    VECTOR_DB_URL: Optional[str] = Field(
        default=None, description="URL or host for Vector DB cluster"
    )
    VECTOR_DB_ENVIRONMENT: Optional[str] = Field(
        default=None, description="Vector DB environment/region tag"
    )
    VECTOR_DB_PATH: str = Field(
        default="./data/vector_store", description="Local persistence path for embedded vector storage"
    )
    VECTOR_DB_INDEX_NAME: str = Field(
        default="abhyas_ai_vectors", description="Vector Index or Collection Name"
    )

    # Hybrid Search Configuration
    HYBRID_SEARCH_ALPHA: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Weight alpha balancing dense vector similarity (alpha) vs BM25 keyword score (1-alpha)",
    )

    # Redis Cache Configuration
    REDIS_HOST: str = Field(default="localhost", description="Redis host address")
    REDIS_PORT: int = Field(default=6379, description="Redis port number")
    REDIS_URL: Optional[str] = Field(
        default="redis://localhost:6379/0", description="Redis connection URL string"
    )
    CACHE_TTL_SECONDS: int = Field(
        default=3600, description="RAG query cache TTL in seconds (1 hour default)"
    )


    # LLM Providers & API Keys
    DEFAULT_LLM_PROVIDER: str = Field(
        default="bedrock", description="Default LLM provider (bedrock, openai, anthropic, gemini)"
    )
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="OpenAI LLM Model Name")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API Key")
    ANTHROPIC_MODEL: str = Field(
        default="claude-3-5-sonnet-20241022", description="Anthropic Claude Model Name"
    )
    COHERE_API_KEY: Optional[str] = Field(
        default=None, description="Cohere API Key for embeddings and reranking"
    )
    GEMINI_API_KEY: Optional[str] = Field(
        default=None, description="Google Gemini API Key"
    )


settings = Settings()

