import os
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings

DEFAULT_JWT_SECRET = "change-me-in-production-use-a-real-secret-key"  # noqa: S105


class Settings(BaseSettings):
    app_name: str = "DocuChat"
    app_version: str = "0.1.0"
    debug: bool = False
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    # Comma-separated additional CORS origins, e.g. "https://docuchat.vercel.app,https://preview.example.com"
    extra_cors_origins: str = ""
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))

    # Cookies — for cross-origin prod (Vercel ↔ Render) set BOTH:
    #   cookie_secure=true, cookie_samesite=none
    # Browsers reject SameSite=None unless Secure is also set.
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./docuchat.db")
    upload_dir: str = "./uploads"
    max_upload_size: int = 20 * 1024 * 1024  # 20MB

    # Storage backend: "local" (uses upload_dir) or "s3" (R2-compatible).
    storage_backend: Literal["local", "s3"] = "local"
    s3_bucket: str = os.getenv("S3_BUCKET", "")
    s3_endpoint_url: str | None = None  # R2: https://<account>.r2.cloudflarestorage.com
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_region: str = "auto"  # R2 expects "auto"

    # Embedding
    embedding_provider: str = "openai"
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Chunking
    chunk_size: int = 1000  # tokens
    chunk_overlap: int = 200  # tokens

    # Auth
    jwt_secret_key: str = DEFAULT_JWT_SECRET
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

    @model_validator(mode="after")
    def _reject_default_jwt_secret_in_prod(self) -> "Settings":
        if not self.debug and self.jwt_secret_key == DEFAULT_JWT_SECRET:
            raise ValueError(
                "JWT_SECRET_KEY is set to the placeholder default. Set a strong "
                "secret (e.g. `python -c 'import secrets; print(secrets.token_urlsafe(64))'`) "
                "or set DEBUG=true if this is a local dev run."
            )
        return self

    @property
    def cors_origins(self) -> list[str]:
        origins = [self.frontend_url]
        if self.extra_cors_origins:
            origins.extend(
                o.strip() for o in self.extra_cors_origins.split(",") if o.strip()
            )
        return origins


settings = Settings()
