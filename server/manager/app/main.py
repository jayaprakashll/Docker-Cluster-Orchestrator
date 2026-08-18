from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from manager.app.api.routes import router
from manager.app.api.scheduler import router as scheduler_router
from manager.app.core.config import settings
from manager.app.database.database import init_db
from manager.app.grpc.server import build_server


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

LOG = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    grpc_server = build_server()
    grpc_server.start()

    LOG.info(
        "manager started: HTTP=%s:%s GPRC=%s:%s DB=%s",
        "0.0.0.0",
        settings.http_port,
        settings.host,
        settings.grpc_port,
        settings.db_url,
    )

    LOG.info(
        "container reconciliation/self-healing is DISABLED"
    )

    try:
        yield
    finally:
        grpc_server.stop(3).wait()
        LOG.info("manager stopped")


app = FastAPI(
    title="Simple Docker Cluster Orchestrator Manager",
    version="1.2.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API ROUTES
# ============================================================

app.include_router(
    router,
    prefix="/api",
)

app.include_router(
    scheduler_router,
    prefix="/api",
)


# ============================================================
# SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "manager.app.main:app",
        host="0.0.0.0",
        port=settings.http_port,
        reload=False,
    )