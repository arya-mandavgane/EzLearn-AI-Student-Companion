from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    ai_provider: str = "gemini"  # "gemini" | "mock"
    ai_mock: bool = False
    ai_mock_invalid: bool = False
    database_url: str = "sqlite:///./study_companion.db"
    secret_key: str = "ai-study-companion-super-secret-jwt-key-2026-production"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    max_file_bytes: int = 10 * 1024 * 1024
    max_pdf_bytes: int = 20 * 1024 * 1024
    max_audio_seconds: int = 60
    max_text_chars: int = 50_000
    max_explain_chars: int = 8_000
    cors_origins: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        return (init_settings, env_settings, dotenv_settings, file_secret_settings)


settings = Settings()
