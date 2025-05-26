from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "SurgeonMatch API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # API
    API_PREFIX: str = "/api/v1"
    API_KEY: str
    API_KEY_HEADER: str = "X-API-Key"
    
    # Database
    DATABASE_URL: str
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str
    REDIS_DEFAULT_TTL: int = 3600  # 1 hour
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Rate Limiting
    RATE_LIMIT: int = 100
    RATE_LIMIT_PERIOD: int = 60  # in seconds
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Global settings instance
settings = get_settings()
