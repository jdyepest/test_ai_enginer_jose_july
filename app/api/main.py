from __future__ import annotations

from fastapi import FastAPI

from app.api.dependencies import settings
from app.api.routes import router
from app.utils.logging import configure_logging

configure_logging(settings().log_level)

app = FastAPI(title="Meeting Intelligence Automation POC", version="0.1.0")
app.include_router(router)

