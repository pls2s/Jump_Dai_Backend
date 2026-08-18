"""Environment-based application settings."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables or a local .env file."""

    app_name: str = "SkillSync AI API"
    app_env: str = "development"
    api_prefix: str = "/api"
    database_url: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    llm_api_key: Optional[str] = None
    typhoon_api_key: Optional[str] = None
    typhoon_model: str = "typhoon-v2.5-30b-a3b-instruct"
    typhoon_base_url: str = "https://api.opentyphoon.ai/v1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
