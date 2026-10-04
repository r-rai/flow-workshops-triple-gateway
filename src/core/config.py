import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "Flo Bank API"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:////app/data/flobank.sqlite")
    API_KEY_SECRET: str = os.getenv("GATE3_API_KEY", "gate3-secret-token")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "flobank-super-secret-signing-key-for-lab")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ISSUER: str = os.getenv("JWT_ISSUER", "https://identity.flobank.internal/realms/flobank")
    API_AUDIENCE: str = os.getenv("API_AUDIENCE", "flobank-api")
    MCP_AUDIENCE: str = os.getenv("MCP_AUDIENCE", "flobank-mcp")
    SEED_FILE_PATH: str = os.getenv("SEED_FILE_PATH", "seed/v1_seed.json")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318/v1/traces")
    ENABLE_TELEMETRY: bool = os.getenv("ENABLE_TELEMETRY", "false").lower() in ("true", "1", "yes")

settings = Settings()
