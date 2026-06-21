from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/loan_manager"
    )
    cors_origins: str = "http://localhost:5173,http://localhost:4173"
    app_name: str = "跨国贷款合同划扣管理系统"

    exchange_rate_api_url: str = (
        "https://api.exchangerate-api.com/v4/latest/CNY"
    )
    exchange_rate_timeout: int = 8
    exchange_rate_max_retries: int = 3
    exchange_rate_backoff: float = 1.2

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
