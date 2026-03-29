"""
Application configuration management using Pydantic BaseSettings.
Loads configuration from environment variables with validation.
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Environment variables should be prefixed with APP_ 
    Example: APP_ENVIRONMENT=production
    """
    
    # Application Settings
    APP_NAME: str = "Tradeskee"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = Field(default="development", description="development, staging, or production")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="Allowed CORS origins"
    )
    
    # Server Settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    WORKERS: int = Field(default=1, description="Number of worker processes")
    
    # Database Settings
    MONGODB_URL: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string"
    )
    MONGODB_DB_NAME: str = Field(
        default="tradeskee_db",
        description="MongoDB database name"
    )
    MONGODB_MIN_POOL_SIZE: int = Field(default=10, description="Minimum connection pool size")
    MONGODB_MAX_POOL_SIZE: int = Field(default=100, description="Maximum connection pool size")
    
    # Redis Settings (for future caching)
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection string (optional)"
    )
    REDIS_CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds")
    
    # External API Keys
    ALPHA_VANTAGE_API_KEY: str = Field(
        default="demo",
        description="Alpha Vantage API key from https://www.alphavantage.co/support/#api-key"
    )
    ALPHA_VANTAGE_BASE_URL: str = "https://www.alphavantage.co/query"
    ALPHA_VANTAGE_RATE_LIMIT: int = Field(
        default=5,
        description="API calls per minute"
    )
    
    # LLM Settings
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    OLLAMA_MODEL: str = Field(
        default="llama2",
        description="Default Ollama model to use"
    )
    LLM_TIMEOUT: int = Field(default=60, description="LLM request timeout in seconds")
    
    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")
    LOG_FORMAT: str = Field(
        default="json",
        description="Log format: json or text"
    )
    
    # Security Settings
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT and encryption"
    )
    API_KEY_HEADER: str = Field(
        default="X-API-Key",
        description="Header name for API key authentication"
    )
    ALLOWED_API_KEYS: list[str] = Field(
        default=[],
        description="List of valid API keys for authentication"
    )
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="Maximum requests per minute per IP"
    )
    
    # AWS Settings (for production deployment)
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )
    ENABLE_METRICS: bool = Field(
        default=True,
        description="Enable Prometheus metrics endpoint"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        """Ensure environment is valid."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Ensure log level is valid."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"
    
    @property
    def database_url(self) -> str:
        """Get formatted database URL."""
        return f"{self.MONGODB_URL}/{self.MONGODB_DB_NAME}"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings
        
    Example:
        >>> from src.core.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.APP_NAME)
    """
    return Settings()


# Export commonly used settings
settings = get_settings()