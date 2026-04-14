from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    deployment_mode: str = "offline_intranet"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    secret_key: str = ""
    kernel_server_auth_token: str = ""
    metadata_backend: str = "postgres"
    sqlite_runtime_allowed: bool = False

    postgres_db: str = "kw_studio"
    postgres_user: str = "kw_studio"
    postgres_password: str = ""
    database_url: str = "postgresql+psycopg://kw_studio:kw_studio@postgres:5432/kw_studio"

    storage_backend: str = "local"
    storage_root: str = "/srv/kw_studio/storage"
    uploads_dir: str = "/srv/kw_studio/storage/uploads"
    artifacts_dir: str = "/srv/kw_studio/storage/artifacts"
    temp_dir: str = "/srv/kw_studio/storage/temp"
    storage_endpoint: str = ""
    storage_bucket: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_region: str = ""
    storage_verify_tls: bool = True

    repository_db_path: str = "./storage/repositories.sqlite3"
    migration_baseline_path: str = "./scripts/migrations/0001_repository_baseline.sql"

    llm_provider: str = "gigachat"
    gigachat_api_base_url: str = ""
    gigachat_auth_url: str = ""
    gigachat_scope: str = "GIGACHAT_API_PERS"
    gigachat_model: str = "GigaChat-Pro"
    gigachat_client_id: str = ""
    gigachat_client_secret: str = ""
    gigachat_timeout_seconds: float = 30.0
    gigachat_verify_ssl: bool = True
    gigachat_ca_cert_path: str = ""
    fake_llm_response: str = "NOOP_LLM_RESPONSE"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
