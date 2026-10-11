import json
from typing import List, Union, Any
from pydantic import field_validator
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
    cors_origins: Union[str, List[str]] = ["*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            clean = v.strip()
            if not clean or clean == "*":
                return ["*"]
            if clean.startswith("[") and clean.endswith("]"):
                try:
                    return json.loads(clean)
                except Exception:
                    pass
            return [x.strip() for x in clean.split(",") if x.strip()]
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
