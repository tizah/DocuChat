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

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
