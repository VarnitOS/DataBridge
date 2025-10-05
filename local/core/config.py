"""
Configuration management for EY Data Integration SaaS
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Snowflake Configuration
    SNOWFLAKE_ACCOUNT: str
    SNOWFLAKE_USER: str
    SNOWFLAKE_PASSWORD: str
    SNOWFLAKE_WAREHOUSE: str
    SNOWFLAKE_DATABASE: str
    SNOWFLAKE_SCHEMA: str = "PUBLIC"
    SNOWFLAKE_ROLE: str = "ACCOUNTADMIN"
    
    # Google Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-pro"
    
    # Application Settings
    APP_NAME: str = "EY Data Integration SaaS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    MAX_FILE_SIZE_MB: int = 500
    ALLOWED_EXTENSIONS: str = "csv,xlsx,xls"
    
    # Agent Configuration
    MAX_GEMINI_AGENTS: int = 3
    MAX_MERGE_AGENTS: int = 10
    MAX_QUALITY_AGENTS: int = 5
    AGENT_TIMEOUT_SECONDS: int = 300
    
    # Mapping Thresholds
    CONFIDENCE_THRESHOLD_HIGH: int = 90
    CONFIDENCE_THRESHOLD_MEDIUM: int = 70
    CONFIDENCE_THRESHOLD_LOW: int = 50
    JIRA_ESCALATION_THRESHOLD: int = 70
    
    # Jira Integration
    JIRA_ENABLED: bool = False
    JIRA_URL: str = ""
    JIRA_EMAIL: str = ""
    JIRA_API_TOKEN: str = ""
    JIRA_PROJECT_KEY: str = "EYDI"
    
    # Datadog Integration
    DATADOG_ENABLED: bool = False
    DATADOG_API_KEY: str = ""
    DATADOG_APP_KEY: str = ""
    DATADOG_SITE: str = "datadoghq.com"
    
    # Snowflake Cost Tracking
    SNOWFLAKE_COST_PER_CREDIT: float = 3.00
    ENABLE_COST_TRACKING: bool = True
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed file extensions as a list"""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

