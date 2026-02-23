"""Configuration management for the receipt analyzer backend."""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Google Sheets configuration
    google_sheets_credentials_path: str = "./credentials.json"
    google_sheets_credentials_b64: str = ""  # Base64-encoded JSON credentials (alternative to file)
    google_sheets_id: str

    # Scraping configuration
    scraping_timeout: int = 30000  # milliseconds

    # Gemini AI configuration
    gemini_api_key: str = ""  # Empty default for testing
    gemini_model: str = "gemini-2.5-flash"
    categories_cache_path: str = "./data/categories.json"
    categories_cache_fuzzy_threshold: int = 80  # 0-100 similarity score

    # Application configuration
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    port: int = 8000  # Render provides this as an environment variable

    # CORS settings
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    frontend_url: str = ""  # Set this for production to allow CORS from your static site

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
