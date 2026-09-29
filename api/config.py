"""
FastAPI Backend Application Configuration.
"""

import os
from typing import List
from pydantic import BaseModel


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class APIConfig(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/smart_factory")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")

    api_port: int = int(os.getenv("API_PORT", "8000"))
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    realtime_interval_seconds: float = float(os.getenv("REALTIME_INTERVAL_SECONDS", "1.0"))
    max_query_limit: int = int(os.getenv("MAX_QUERY_LIMIT", "1000"))
    default_history_limit: int = int(os.getenv("DEFAULT_HISTORY_LIMIT", "100"))
