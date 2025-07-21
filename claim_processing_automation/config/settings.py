from pydantic import BaseSettings, Field
from typing import Optional, List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Configuration
    app_name: str = Field(default="Claim Processing Automation", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Database Configuration
    database_url: str = Field(env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # OpenAI Configuration
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    
    # Anthropic Configuration
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Stripe Configuration
    stripe_secret_key: str = Field(env="STRIPE_SECRET_KEY")
    stripe_publishable_key: str = Field(env="STRIPE_PUBLISHABLE_KEY")
    stripe_webhook_secret: str = Field(env="STRIPE_WEBHOOK_SECRET")
    
    # JWT Configuration
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Email Configuration
    sendgrid_api_key: Optional[str] = Field(default=None, env="SENDGRID_API_KEY")
    from_email: str = Field(default="noreply@yourcompany.com", env="FROM_EMAIL")
    
    # File Storage Configuration
    upload_folder: str = Field(default="./uploads", env="UPLOAD_FOLDER")
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    allowed_extensions: List[str] = Field(
        default=["pdf", "png", "jpg", "jpeg"], 
        env="ALLOWED_EXTENSIONS"
    )
    
    # OCR Configuration
    tesseract_cmd: str = Field(default="/usr/bin/tesseract", env="TESSERACT_CMD")
    poppler_path: str = Field(default="/usr/bin", env="POPPLER_PATH")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="app.log", env="LOG_FILE")
    
    # Background Task Configuration
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    # Cloud Storage Configuration (Optional)
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_bucket_name: Optional[str] = Field(default=None, env="AWS_BUCKET_NAME")
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    
    google_application_credentials: Optional[str] = Field(default=None, env="GOOGLE_APPLICATION_CREDENTIALS")
    gcs_bucket_name: Optional[str] = Field(default=None, env="GCS_BUCKET_NAME")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")
    
    # Monitoring
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    health_check_endpoint: str = Field(default="/health", env="HEALTH_CHECK_ENDPOINT")
    
    # LLM Processing Configuration
    max_tokens: int = Field(default=4000, env="MAX_TOKENS")
    temperature: float = Field(default=0.1, env="TEMPERATURE")
    
    # Claim Processing Configuration
    max_claim_amount: float = Field(default=100000.0, env="MAX_CLAIM_AMOUNT")
    auto_approve_threshold: float = Field(default=1000.0, env="AUTO_APPROVE_THRESHOLD")
    manual_review_threshold: float = Field(default=50000.0, env="MANUAL_REVIEW_THRESHOLD")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure upload directory exists
        Path(self.upload_folder).mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()


# Development and Production specific configurations
class DevelopmentSettings(Settings):
    """Development environment specific settings."""
    debug: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """Production environment specific settings."""
    debug: bool = False
    log_level: str = "WARNING"


def get_settings() -> Settings:
    """Get settings based on environment."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    else:
        return DevelopmentSettings()