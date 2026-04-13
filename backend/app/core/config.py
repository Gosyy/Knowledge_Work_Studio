from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    secret_key: str = "change-me"
    kernel_server_auth_token: str = ""
    metadata_backend: str = "postgres"
    sqlite_runtime_allowed: bool = False

    postgres_db: str = "kw_studio"
    postgres_user: str = "kw_studio"
    postgres_password: str = "kw_studio"
    database_url: str = "postgresql+psycopg://kw_studio:kw_studio@postgres:5432/kw_studio"

    storage_root: str = "./storage"
    uploads_dir: str = "./storage/uploads"
    artifacts_dir: str = "./storage/artifacts"
    temp_dir: str = "./storage/temp"
    repository_db_path: str = "./storage/repositories.sqlite3"
    migration_baseline_path: str = "./scripts/migrations/0001_repository_baseline.sql"
    llm_provider: str = "gigachat"
    gigachat_api_base_url: str = "https://gigachat.example.local"
    gigachat_model: str = "GigaChat-Pro"
    gigachat_client_id: str = ""
    gigachat_client_secret: str = ""
    fake_llm_response: str = "NOOP_LLM_RESPONSE"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
