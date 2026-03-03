from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "DocuChat"
    app_version: str = "0.1.0"
    debug: bool = False
    frontend_url: str = "http://localhost:3000"
    backend_port: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
