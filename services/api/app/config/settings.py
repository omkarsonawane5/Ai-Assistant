from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Assistant API"
    app_env: str = "local"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    database_url: str = "postgresql+asyncpg://assistant:assistant@localhost:5432/assistant"
    secret_key: str = "change-me-in-local-env"
    access_token_expire_minutes: int = 60 * 24
    dev_bootstrap_user_email: str = "local@example.com"
    dev_bootstrap_user_password: str = "local-password"
    ai_provider: str = "fake"
    ai_model: str = "fake-local"
    ai_api_key: str | None = None
    assistant_system_prompt: str = "You are a helpful, concise AI assistant."
    recent_message_limit: int = 20

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

@lru_cache
def get_settings() -> Settings:
    return Settings()
