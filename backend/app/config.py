"""
Centralized application configuration.
Loads values from environment variables (see .env.example).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/expense_manager"

    # Auth
    JWT_SECRET_KEY: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # AI
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""  # optional: alternate provider for local dev/testing
    LLM_PROVIDER: str = "gemini"  # "gemini" or "anthropic"

    # Storage
    STORAGE_PROVIDER: str = "local"  # "local" or "cloudinary"
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"

    # Uploads
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
