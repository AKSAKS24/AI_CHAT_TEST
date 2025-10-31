from pydantic import BaseModel, Field
from typing import List
import os, json
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    APP_NAME: str = os.getenv("APP_NAME", "OData AI Backend")
    APP_ENV: str = os.getenv("APP_ENV", "dev")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: json.loads(os.getenv("CORS_ORIGINS", "[\"*\"]")))

    SAP_BASE_URL: str = os.getenv("SAP_BASE_URL", "").rstrip("/")
    SAP_AUTH_MODE: str = os.getenv("SAP_AUTH_MODE", "basic")
    SAP_USERNAME: str = os.getenv("SAP_USERNAME", "")
    SAP_PASSWORD: str = os.getenv("SAP_PASSWORD", "")
    SAP_OAUTH_TOKEN_URL: str = os.getenv("SAP_OAUTH_TOKEN_URL", "")
    SAP_OAUTH_CLIENT_ID: str = os.getenv("SAP_OAUTH_CLIENT_ID", "")
    SAP_OAUTH_CLIENT_SECRET: str = os.getenv("SAP_OAUTH_CLIENT_SECRET", "")
    SAP_OAUTH_SCOPE: str = os.getenv("SAP_OAUTH_SCOPE", "openid")

    USE_LANGCHAIN: bool = os.getenv("USE_LANGCHAIN", "false").lower() == "true"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")

settings = Settings()
