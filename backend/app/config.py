from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "DocuChat"
    app_version: str = "0.1.0"
    debug: bool = False
    frontend_url: str = "http://localhost:3000"
    # Comma-separated additional CORS origins, e.g. "https://docuchat.vercel.app,https://preview.example.com"
    extra_cors_origins: str = ""
    backend_port: int = 8000

    # Cookies — for cross-origin prod (Vercel ↔ Render) set BOTH:
    #   cookie_secure=true, cookie_samesite=none
    # Browsers reject SameSite=None unless Secure is also set.
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    database_url: str = "sqlite+aiosqlite:///./docuchat.db"
    upload_dir: str = "./uploads"
    max_upload_size: int = 20 * 1024 * 1024  # 20MB

    # Storage backend: "local" (uses upload_dir) or "s3" (R2-compatible).
    storage_backend: Literal["local", "s3"] = "local"
    s3_bucket: str = ""
    s3_endpoint_url: str | None = None  # R2: https://<account>.r2.cloudflarestorage.com
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_region: str = "auto"  # R2 expects "auto"

    # Embedding
    embedding_provider: str = "openai"
    openai_api_key: str | None = "REDACTED_OPENAI_KEY"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Chunking
    chunk_size: int = 1000  # tokens
    chunk_overlap: int = 200  # tokens

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

    @property
    def cors_origins(self) -> list[str]:
        origins = [self.frontend_url]
        if self.extra_cors_origins:
            origins.extend(
                o.strip() for o in self.extra_cors_origins.split(",") if o.strip()
            )
        return origins


settings = Settings()
