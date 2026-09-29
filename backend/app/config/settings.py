import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings loaded from environment variables or defaults."""

    app_name: str = "PromoNxtAI"
    env: str = "development"
    debug: bool = True
    use_sample_data: bool = True
    image_mock: bool = True
    n8n_mock: bool = True
    llm_mock: bool = True

    # OpenRouter configuration
    openrouter_api_key: str = "mock-key"
    openrouter_text_model: str = "google/gemini-2.5-flash"
    openrouter_image_model: str = "black-forest-labs/flux.2-klein-4b"
    openrouter_site_url: str = "https://promonxtai.com"
    openrouter_site_name: str = "PromoNxtAI"

    # Supabase configuration
    supabase_url: str = "https://your-project.supabase.co"
    supabase_key: str = "mock-key"
    supabase_db_url: str = (
        "postgresql://postgres:password@db.your-project.supabase.co:5432/postgres"
    )

    # n8n configuration
    n8n_webhook_url: str = "https://your-n8n-instance.com/webhook/instagram-publish"
    n8n_shared_secret: str = "your_n8n_shared_secret_here"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
