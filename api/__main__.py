"""
Entrypoint to run FastAPI server locally via `python -m api`.
"""

import uvicorn
from api.config import APIConfig

if __name__ == "__main__":
    cfg = APIConfig()
    print(f"Starting Smart Factory FastAPI server on http://{cfg.api_host}:{cfg.api_port}...")
    uvicorn.run("api.main:app", host=cfg.api_host, port=cfg.api_port, reload=True)
