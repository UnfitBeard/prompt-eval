# config.py
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    # MongoDB
    MONGO_DB_URI: str = Field(
        default=..., description="MongoDB connection URI")
    # Default DB used by this repo's Mongo datasets.
    # Can be overridden via env var MONGO_DB_NAME.
    MONGO_DB_NAME: str = "PromptEval"

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default=..., description="Secret key for JWT tokens")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Gemini API (for existing chatbot)
    GEMINI_API_KEY: str = Field(
        default=..., description="Google Gemini API key")

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:4200", "http://localhost:3000"]
    FRONTEND_URL: str = "http://localhost:4200"

    # Application
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # File paths
    STATIC_FILES_DIR: str = "static"
    UPLOAD_DIR: str = "uploads"

    # Security
    SECRET_KEY: str = Field(default=..., description="App secret key")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # This allows extra fields in .env without errors

    @validator("MONGO_DB_URI")
    def validate_mongo_uri(cls, v):
        if not v:
            raise ValueError("MONGO_DB_URI is required")
        return v

    @validator("JWT_SECRET_KEY", "SECRET_KEY", "GEMINI_API_KEY")
    def validate_secret_key(cls, v):
        if not v:
            raise ValueError("Required field is missing")
        return v


# Global settings instance
settings = Settings()
