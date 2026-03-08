from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "DocuChat"
    app_version: str = "0.1.0"
    debug: bool = False
    frontend_url: str = "http://localhost:3000"
    backend_port: int = 8000
    database_url: str = "sqlite+aiosqlite:///./docuchat.db"
    upload_dir: str = "./uploads"
    max_upload_size: int = 20 * 1024 * 1024  # 20MB

    # Embedding
    embedding_provider: str = "openai"
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Chunking
    chunk_size: int = 1000  # tokens
    chunk_overlap: int = 200  # tokens

    # Vector store
    chroma_persist_dir: str = "./chroma_data"

    # Auth
    jwt_secret_key: str = "change-me-in-production-use-a-real-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    chat_rate_limit: int = 20  # messages per minute per user

    # LLM
    llm_provider: str = "openai"
    anthropic_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    anthropic_chat_model: str = "claude-sonnet-4-20250514"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
