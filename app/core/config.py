"""
Configuration settings for SRM Guide Bot
"""

import os
from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import validator, Field

logger = None


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    ENVIRONMENT: str = Field(default="development", description="Environment (development/production)")
    DEBUG: bool = Field(default=True, description="Debug mode")
    HOST: str = Field(default="0.0.0.0", description="Host to bind to")
    PORT: int = Field(default=8000, description="Port to bind to")
    
    # Security
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration in days")
    REFRESH_TOKEN_SECRET: str = Field(default="", description="Refresh token secret")
    
    # Database
    DATABASE_URL: str = Field(default="mongodb://localhost:27017/srm_guide_bot", description="MongoDB connection URL")
    DATABASE_URL_TEST: str = Field(default="mongodb://localhost:27017/srm_guide_bot_test", description="Test MongoDB connection URL")
    MONGO_URI: str = Field(default="mongodb://localhost:27017", description="MongoDB connection URI")
    MONGO_DB_NAME: str = Field(default="srm_guide_bot", description="MongoDB database name")
    MONGO_USERNAME: str = Field(default="", description="MongoDB username")
    MONGO_PASSWORD: str = Field(default="", description="MongoDB password")
    SQL_DATABASE_URL: str = Field(default="sqlite:///./mist.db", description="SQLAlchemy database URL")
    SQL_DATABASE_URL_ASYNC: Optional[str] = Field(default=None, description="Optional async SQLAlchemy URL override")
    SQL_ECHO: bool = Field(default=False, description="Enable SQLAlchemy engine echo logging")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    REDIS_PASSWORD: str = Field(default="", description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    
    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:5173", description="CORS origins")
    ALLOWED_HOSTS: str = Field(default="*", description="Allowed hosts")
    
    # OpenAI
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-4", description="OpenAI model to use")
    OPENAI_MAX_TOKENS: int = Field(default=2000, description="Maximum tokens for OpenAI")
    OPENAI_TEMPERATURE: float = Field(default=0.7, description="OpenAI temperature")
    
    # Email
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP host")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USER: str = Field(default="", description="SMTP username")
    SMTP_PASSWORD: str = Field(default="", description="SMTP password")
    SMTP_FROM_EMAIL: str = Field(default="noreply@srmguidebot.com", description="From email")
    SMTP_FROM_NAME: str = Field(default="SRM Guide Bot", description="From name")
    
    # File Upload
    MAX_FILE_SIZE: int = Field(default=5242880, description="Maximum file size in bytes")
    ALLOWED_FILE_TYPES: str = Field(default="image/jpeg,image/png,image/gif,application/pdf", description="Allowed file types")
    UPLOAD_DIR: str = Field(default="uploads", description="Upload directory")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    LOG_FILE: str = Field(default="logs/app.log", description="Log file path")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Rate limit per minute")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, description="Rate limit per hour")
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", description="Celery result backend")
    
    # Session
    SESSION_SECRET: str = Field(default="", description="Session secret")
    
    # Web Scraping
    SCRAPING_ENABLED: bool = Field(default=True, description="Enable web scraping")
    SCRAPING_INTERVAL_HOURS: int = Field(default=24, description="Scraping interval in hours")
    USER_AGENT: str = Field(default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", description="User agent for scraping")
    
    # SRM Portal Credentials (for scraping)
    SRM_PORTAL_BASE_URL: str = Field(default="https://sp.srmist.edu.in/srmiststudentportal", description="SRM portal base URL")
    SRM_MAIN_URL: str = Field(default="https://www.srmist.edu.in", description="SRM main website URL")
    
    # Password Policy
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")
    PASSWORD_REQUIRE_SPECIAL_CHARS: bool = Field(default=True, description="Require special characters in password")
    PASSWORD_REQUIRE_NUMBERS: bool = Field(default=True, description="Require numbers in password")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True, description="Require uppercase letters in password")
    
    # Cache
    CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds")
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        if v not in ["development", "production", "testing"]:
            raise ValueError("ENVIRONMENT must be development, production, or testing")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("ALLOWED_FILE_TYPES", pre=True)
    def parse_allowed_file_types(cls, v):
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Production validation
        if self.ENVIRONMENT == "production":
            if not self.SECRET_KEY or self.SECRET_KEY == "your-super-secret-key-change-this-in-production":
                raise ValueError("SECRET_KEY must be set in production")
            if not self.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY must be set in production")


# Create settings instance
settings = Settings()
